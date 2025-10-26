from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional

from ..core.models import Address, ApiSource, FlipResult, PropertyData, RentalResult
from ..utils.config import settings
from ..utils.logging import logger


@dataclass(slots=True)
class AnalysisSnapshot:
    analysis_type: str
    purchase_price: float
    assumptions: Dict[str, Any]
    result: Dict[str, Any]
    created_at: datetime


_database_path: str | None = None
_shared_connection: sqlite3.Connection | None = None
_repository: "PropertyRepository" | None = None


def _normalize_address(address: Address) -> Address:
    return Address(
        line1=address.line1.strip().upper(),
        city=address.city.strip().upper(),
        state=address.state.strip().upper(),
        zip=address.zip.strip(),
    )


def _resolve_database_path(database_url: str) -> str:
    url = database_url.strip()
    if not url:
        raise ValueError("DATABASE_URL must be configured")

    if url.endswith(":memory:"):
        return ":memory:"

    prefixes = ("sqlite+pysqlite://", "sqlite://")
    if not url.startswith(prefixes):
        raise ValueError(f"Unsupported database URL '{database_url}'")

    # Normalise the prefix to make parsing easier.
    if url.startswith("sqlite+pysqlite://"):
        remainder = url[len("sqlite+pysqlite://") :]
    else:
        remainder = url[len("sqlite://") :]

    if not remainder:
        return ":memory:"

    if remainder.startswith("/"):
        # Collapse multiple leading slashes for absolute paths (e.g. '////tmp/db.sqlite').
        while remainder.startswith("//"):
            remainder = remainder[1:]
        return "/" + remainder.lstrip("/")

    return remainder


def _serialise_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def _deserialise_json(raw: str | None) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        logger.debug("Ignoring malformed JSON payload: %s", raw)
    return {}


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            line1 TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            zip TEXT NOT NULL,
            beds REAL,
            baths REAL,
            sqft INTEGER,
            lot_sqft INTEGER,
            year_built INTEGER,
            market_value_estimate REAL,
            rent_estimate REAL,
            annual_taxes REAL,
            closing_cost_estimate REAL,
            meta TEXT NOT NULL DEFAULT '{}',
            UNIQUE(line1, city, state, zip)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS property_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER NOT NULL,
            source TEXT NOT NULL,
            FOREIGN KEY(property_id) REFERENCES properties(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS analysis_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER NOT NULL,
            analysis_type TEXT NOT NULL,
            purchase_price REAL NOT NULL,
            noi_annual REAL,
            annual_debt_service REAL,
            cash_flow_annual REAL,
            cap_rate_pct REAL,
            irr_pct REAL,
            arv REAL,
            total_costs REAL,
            projected_profit REAL,
            margin_pct REAL,
            suggested_purchase_price REAL,
            assumptions TEXT NOT NULL,
            result_snapshot TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(property_id) REFERENCES properties(id) ON DELETE CASCADE
        )
        """
    )
    conn.commit()


def _create_connection() -> sqlite3.Connection:
    global _shared_connection

    if _database_path is None:
        raise RuntimeError("Database has not been configured")

    if _database_path == ":memory:":
        if _shared_connection is None:
            _shared_connection = sqlite3.connect(
                ":memory:", detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False
            )
            _shared_connection.row_factory = sqlite3.Row
            _ensure_schema(_shared_connection)
        return _shared_connection

    db_path = Path(_database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(
        str(db_path), detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    _ensure_schema(conn)
    return conn


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    conn = _create_connection()
    try:
        yield conn
        conn.commit()
    finally:
        if conn is not _shared_connection:
            conn.close()


def init_engine(database_url: Optional[str] = None) -> str:
    global _database_path, _shared_connection

    resolved_url = database_url or settings.DATABASE_URL
    if not resolved_url:
        raise ValueError("DATABASE_URL must be configured")

    database_path = _resolve_database_path(resolved_url)
    if _database_path == database_path:
        return database_path

    if _shared_connection is not None:
        _shared_connection.close()
        _shared_connection = None

    _database_path = database_path

    with _connection():
        pass

    logger.debug("Initialised database engine at %s", resolved_url)
    return database_path


class PropertyRepository:
    """Repository encapsulating persistence for property and analysis data."""

    def __init__(self) -> None:
        if _database_path is None:
            init_engine()

    def get_property(self, address: Address) -> Optional[PropertyData]:
        normalized = _normalize_address(address)
        with _connection() as conn:
            record = self._get_record(conn, normalized)
            if record is None:
                return None
            return self._record_to_domain(conn, record)

    def upsert_property(self, data: PropertyData) -> PropertyData:
        normalized = _normalize_address(data.address)
        with _connection() as conn:
            record = self._get_record(conn, normalized)
            merged_meta = self._merge_meta(record, data.meta)
            payload = self._property_payload(normalized, data, merged_meta)

            if record is None:
                cursor = conn.execute(
                    """
                    INSERT INTO properties (
                        line1, city, state, zip, beds, baths, sqft, lot_sqft, year_built,
                        market_value_estimate, rent_estimate, annual_taxes,
                        closing_cost_estimate, meta
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    payload,
                )
                assert cursor.lastrowid is not None
                property_id = int(cursor.lastrowid)
            else:
                property_id = record["id"]
                conn.execute(
                    """
                    UPDATE properties
                    SET line1=?, city=?, state=?, zip=?, beds=?, baths=?, sqft=?, lot_sqft=?,
                        year_built=?, market_value_estimate=?, rent_estimate=?, annual_taxes=?,
                        closing_cost_estimate=?, meta=?
                    WHERE id=?
                    """,
                    payload + (property_id,),
                )

            self._replace_sources(conn, property_id, data.sources)
            refreshed = conn.execute(
                "SELECT * FROM properties WHERE id = ?", (property_id,)
            ).fetchone()
            assert refreshed is not None
            return self._record_to_domain(conn, refreshed)

    def record_analysis(
        self,
        property_data: PropertyData,
        analysis_type: str,
        purchase_price: float,
        assumptions: Dict[str, Any],
        result: RentalResult | FlipResult,
    ) -> None:
        normalized = _normalize_address(property_data.address)
        snapshot = result.model_dump()
        analysis_type_normalized = analysis_type.lower()

        with _connection() as conn:
            record = self._get_record(conn, normalized)
            merged_meta = self._merge_meta(record, property_data.meta)
            payload = self._property_payload(normalized, property_data, merged_meta)

            if record is None:
                cursor = conn.execute(
                    """
                    INSERT INTO properties (
                        line1, city, state, zip, beds, baths, sqft, lot_sqft, year_built,
                        market_value_estimate, rent_estimate, annual_taxes,
                        closing_cost_estimate, meta
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    payload,
                )
                assert cursor.lastrowid is not None
                property_id = int(cursor.lastrowid)
            else:
                property_id = record["id"]
                conn.execute(
                    """
                    UPDATE properties
                    SET line1=?, city=?, state=?, zip=?, beds=?, baths=?, sqft=?, lot_sqft=?,
                        year_built=?, market_value_estimate=?, rent_estimate=?, annual_taxes=?,
                        closing_cost_estimate=?, meta=?
                    WHERE id=?
                    """,
                    payload + (property_id,),
                )

            self._replace_sources(conn, property_id, property_data.sources)

            created_at = datetime.now(UTC).replace(microsecond=0).isoformat()
            conn.execute(
                """
                INSERT INTO analysis_runs (
                    property_id, analysis_type, purchase_price, noi_annual, annual_debt_service,
                    cash_flow_annual, cap_rate_pct, irr_pct, arv, total_costs, projected_profit,
                    margin_pct, suggested_purchase_price, assumptions, result_snapshot, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    property_id,
                    analysis_type_normalized,
                    float(purchase_price),
                    snapshot.get("noi_annual"),
                    snapshot.get("annual_debt_service"),
                    snapshot.get("cash_flow_annual"),
                    snapshot.get("cap_rate_pct"),
                    snapshot.get("irr_pct"),
                    snapshot.get("arv"),
                    snapshot.get("total_costs"),
                    snapshot.get("projected_profit"),
                    snapshot.get("margin_pct"),
                    snapshot.get("suggested_purchase_price"),
                    _serialise_json(dict(assumptions or {})),
                    _serialise_json(snapshot),
                    created_at,
                ),
            )

    def list_analyses(
        self,
        address: Address,
        *,
        limit: int = 10,
        analysis_type: Optional[str] = None,
    ) -> List[AnalysisSnapshot]:
        normalized = _normalize_address(address)
        with _connection() as conn:
            record = self._get_record(conn, normalized)
            if record is None:
                return []

            params: List[Any] = [record["id"]]
            query = [
                "SELECT analysis_type, purchase_price, assumptions, result_snapshot, created_at",
                "FROM analysis_runs",
                "WHERE property_id = ?",
            ]

            if analysis_type:
                query.append("AND analysis_type = ?")
                params.append(analysis_type.lower())

            query.append("ORDER BY created_at DESC")
            query.append("LIMIT ?")
            params.append(max(limit, 1))

            rows = conn.execute(" ".join(query), params).fetchall()

            snapshots: List[AnalysisSnapshot] = []
            for row in rows:
                created_at_raw = row["created_at"]
                try:
                    created_at = datetime.fromisoformat(created_at_raw)
                except ValueError:
                    created_at = datetime.now(UTC)

                snapshots.append(
                    AnalysisSnapshot(
                        analysis_type=row["analysis_type"],
                        purchase_price=float(row["purchase_price"]),
                        assumptions=_deserialise_json(row["assumptions"]),
                        result=_deserialise_json(row["result_snapshot"]),
                        created_at=created_at,
                    )
                )
            return snapshots

    def _get_record(self, conn: sqlite3.Connection, address: Address) -> sqlite3.Row | None:
        return conn.execute(
            """
            SELECT * FROM properties
            WHERE line1 = ? AND city = ? AND state = ? AND zip = ?
            """,
            (address.line1, address.city, address.state, address.zip),
        ).fetchone()

    def _record_to_domain(self, conn: sqlite3.Connection, record: sqlite3.Row) -> PropertyData:
        sources = conn.execute(
            "SELECT source FROM property_sources WHERE property_id = ? ORDER BY source", (record["id"],)
        ).fetchall()

        api_sources: List[ApiSource] = []
        for source_row in sources:
            try:
                api_sources.append(ApiSource(source_row["source"]))
            except ValueError:
                logger.debug(
                    "Ignoring unknown source '%s' while hydrating property", source_row["source"]
                )

        return PropertyData(
            address=Address(
                line1=record["line1"],
                city=record["city"],
                state=record["state"],
                zip=record["zip"],
            ),
            beds=record["beds"],
            baths=record["baths"],
            sqft=record["sqft"],
            lot_sqft=record["lot_sqft"],
            year_built=record["year_built"],
            market_value_estimate=record["market_value_estimate"],
            rent_estimate=record["rent_estimate"],
            annual_taxes=record["annual_taxes"],
            closing_cost_estimate=record["closing_cost_estimate"],
            meta=_deserialise_json(record["meta"]),
            sources=api_sources,
        )

    def _property_payload(
        self,
        normalized: Address,
        data: PropertyData,
        merged_meta: Dict[str, Any],
    ) -> tuple:
        return (
            normalized.line1,
            normalized.city,
            normalized.state,
            normalized.zip,
            data.beds,
            data.baths,
            data.sqft,
            data.lot_sqft,
            data.year_built,
            data.market_value_estimate,
            data.rent_estimate,
            data.annual_taxes,
            data.closing_cost_estimate,
            _serialise_json(merged_meta),
        )

    def _merge_meta(self, record: sqlite3.Row | None, new_meta: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        existing = _deserialise_json(record["meta"]) if record is not None else {}
        incoming = dict(new_meta or {})
        existing.update({key: value for key, value in incoming.items() if value is not None})
        return existing

    def _replace_sources(self, conn: sqlite3.Connection, property_id: int, sources: Iterable[ApiSource]) -> None:
        unique_sources = sorted({source.value for source in sources})
        conn.execute("DELETE FROM property_sources WHERE property_id = ?", (property_id,))
        for source in unique_sources:
            conn.execute(
                "INSERT INTO property_sources (property_id, source) VALUES (?, ?)",
                (property_id, source),
            )


def get_repository() -> PropertyRepository:
    global _repository
    if _repository is None:
        _repository = PropertyRepository()
    return _repository


def configure(database_url: str) -> None:
    global _repository
    init_engine(database_url)
    _repository = PropertyRepository()
