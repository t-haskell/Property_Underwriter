from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
    func,
    select,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)
from sqlalchemy.pool import StaticPool

from ..core.models import Address, ApiSource, FlipResult, PropertyData, RentalResult
from ..utils.config import settings
from ..utils.logging import logger


class Base(DeclarativeBase):
    """Declarative base for persistence models."""


class PropertyRecord(Base):
    __tablename__ = "properties"
    __table_args__ = (
        UniqueConstraint("line1", "city", "state", "zip", name="uq_properties_address"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    line1: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(2), nullable=False)
    zip: Mapped[str] = mapped_column(String(20), nullable=False)
    beds: Mapped[float | None] = mapped_column(Float, nullable=True)
    baths: Mapped[float | None] = mapped_column(Float, nullable=True)
    sqft: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lot_sqft: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year_built: Mapped[int | None] = mapped_column(Integer, nullable=True)
    market_value_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)
    rent_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)
    annual_taxes: Mapped[float | None] = mapped_column(Float, nullable=True)
    closing_cost_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)
    meta: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    sources: Mapped[List["PropertySourceRecord"]] = relationship(
        "PropertySourceRecord",
        back_populates="property",
        cascade="all, delete-orphan",
    )
    analyses: Mapped[List["AnalysisRunRecord"]] = relationship(
        "AnalysisRunRecord",
        back_populates="property",
        cascade="all, delete-orphan",
    )


class PropertySourceRecord(Base):
    __tablename__ = "property_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id", ondelete="CASCADE"))
    source: Mapped[str] = mapped_column(String(64), nullable=False)

    property: Mapped[PropertyRecord] = relationship("PropertyRecord", back_populates="sources")


class AnalysisRunRecord(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id", ondelete="CASCADE"))
    analysis_type: Mapped[str] = mapped_column(String(16), nullable=False)
    purchase_price: Mapped[float] = mapped_column(Float, nullable=False)
    noi_annual: Mapped[float | None] = mapped_column(Float, nullable=True)
    annual_debt_service: Mapped[float | None] = mapped_column(Float, nullable=True)
    cash_flow_annual: Mapped[float | None] = mapped_column(Float, nullable=True)
    cap_rate_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    irr_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    arv: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_costs: Mapped[float | None] = mapped_column(Float, nullable=True)
    projected_profit: Mapped[float | None] = mapped_column(Float, nullable=True)
    margin_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    suggested_purchase_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    assumptions: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    result_snapshot: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    property: Mapped[PropertyRecord] = relationship("PropertyRecord", back_populates="analyses")


@dataclass(slots=True)
class AnalysisSnapshot:
    analysis_type: str
    purchase_price: float
    assumptions: Dict[str, Any]
    result: Dict[str, Any]
    created_at: datetime


_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None
_repository: "PropertyRepository" | None = None


def _normalize_address(address: Address) -> Address:
    return Address(
        line1=address.line1.strip().upper(),
        city=address.city.strip().upper(),
        state=address.state.strip().upper(),
        zip=address.zip.strip(),
    )


def _create_engine(database_url: str) -> Engine:
    connect_args: Dict[str, Any] = {}
    engine_kwargs: Dict[str, Any] = {"future": True, "echo": False}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        engine_kwargs["connect_args"] = connect_args
        if ":memory:" in database_url:
            engine_kwargs["poolclass"] = StaticPool
    return create_engine(database_url, **engine_kwargs)


def init_engine(database_url: Optional[str] = None) -> Engine:
    """Initialise the SQLAlchemy engine and session factory."""

    global _engine, _session_factory

    database_url = database_url or settings.DATABASE_URL
    if not database_url:
        raise ValueError("DATABASE_URL must be configured")

    if _engine is not None:
        current_url = str(_engine.url)
        if current_url == database_url:
            return _engine
        _engine.dispose()

    _engine = _create_engine(database_url)
    Base.metadata.create_all(_engine)
    _session_factory = sessionmaker(bind=_engine, expire_on_commit=False, autoflush=False, future=True)
    logger.debug("Initialised database engine at %s", database_url)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        init_engine()
    assert _session_factory is not None
    return _session_factory


class PropertyRepository:
    """Repository encapsulating persistence for property and analysis data."""

    def __init__(self, session_factory: Optional[sessionmaker[Session]] = None) -> None:
        self._session_factory = session_factory or get_session_factory()

    def get_property(self, address: Address) -> Optional[PropertyData]:
        normalized = _normalize_address(address)
        with self._session_factory() as session:
            record = self._get_record(session, normalized)
            if record is None:
                return None
            return self._record_to_domain(record)

    def upsert_property(self, data: PropertyData) -> PropertyData:
        normalized = _normalize_address(data.address)
        with self._session_factory() as session:
            record = self._get_record(session, normalized)
            if record is None:
                record = PropertyRecord(
                    line1=normalized.line1,
                    city=normalized.city,
                    state=normalized.state,
                    zip=normalized.zip,
                )
                session.add(record)
            self._apply_property_data(record, data, normalized)
            session.commit()
            session.refresh(record)
            return self._record_to_domain(record)

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

        with self._session_factory() as session:
            record = self._get_record(session, normalized)
            if record is None:
                record = PropertyRecord(
                    line1=normalized.line1,
                    city=normalized.city,
                    state=normalized.state,
                    zip=normalized.zip,
                )
                session.add(record)
            self._apply_property_data(record, property_data, normalized)
            session.flush()

            run = AnalysisRunRecord(
                property_id=record.id,
                analysis_type=analysis_type_normalized,
                purchase_price=float(purchase_price),
                noi_annual=snapshot.get("noi_annual"),
                annual_debt_service=snapshot.get("annual_debt_service"),
                cash_flow_annual=snapshot.get("cash_flow_annual"),
                cap_rate_pct=snapshot.get("cap_rate_pct"),
                irr_pct=snapshot.get("irr_pct"),
                arv=snapshot.get("arv"),
                total_costs=snapshot.get("total_costs"),
                projected_profit=snapshot.get("projected_profit"),
                margin_pct=snapshot.get("margin_pct"),
                suggested_purchase_price=snapshot.get("suggested_purchase_price"),
                assumptions=dict(assumptions),
                result_snapshot=snapshot,
            )
            session.add(run)
            session.commit()

    def list_analyses(
        self,
        address: Address,
        *,
        limit: int = 10,
        analysis_type: Optional[str] = None,
    ) -> List[AnalysisSnapshot]:
        normalized = _normalize_address(address)
        with self._session_factory() as session:
            record = self._get_record(session, normalized)
            if record is None:
                return []

            stmt = select(AnalysisRunRecord).where(AnalysisRunRecord.property_id == record.id)
            if analysis_type:
                stmt = stmt.where(AnalysisRunRecord.analysis_type == analysis_type.lower())
            stmt = stmt.order_by(AnalysisRunRecord.created_at.desc()).limit(max(limit, 1))
            rows = session.execute(stmt).scalars().all()

            snapshots: List[AnalysisSnapshot] = []
            for row in rows:
                created_at = row.created_at
                if created_at is None:
                    session.refresh(row)
                    created_at = row.created_at or datetime.utcnow()
                snapshots.append(
                    AnalysisSnapshot(
                        analysis_type=row.analysis_type,
                        purchase_price=row.purchase_price,
                        assumptions=row.assumptions,
                        result=row.result_snapshot,
                        created_at=created_at,
                    )
                )
            return snapshots

    def _get_record(self, session: Session, address: Address) -> Optional[PropertyRecord]:
        stmt = select(PropertyRecord).where(
            PropertyRecord.line1 == address.line1,
            PropertyRecord.city == address.city,
            PropertyRecord.state == address.state,
            PropertyRecord.zip == address.zip,
        )
        return session.execute(stmt).scalar_one_or_none()

    def _apply_property_data(
        self,
        record: PropertyRecord,
        data: PropertyData,
        normalized: Address,
    ) -> None:
        record.line1 = normalized.line1
        record.city = normalized.city
        record.state = normalized.state
        record.zip = normalized.zip
        record.beds = data.beds
        record.baths = data.baths
        record.sqft = data.sqft
        record.lot_sqft = data.lot_sqft
        record.year_built = data.year_built
        record.market_value_estimate = data.market_value_estimate
        record.rent_estimate = data.rent_estimate
        record.annual_taxes = data.annual_taxes
        record.closing_cost_estimate = data.closing_cost_estimate

        existing_meta: Dict[str, Any] = dict(record.meta or {})
        new_meta: Dict[str, Any] = dict(data.meta or {})
        existing_meta.update({key: value for key, value in new_meta.items() if value is not None})
        record.meta = existing_meta

        unique_sources = sorted({source.value for source in data.sources})
        record.sources = [PropertySourceRecord(source=src) for src in unique_sources]

    def _record_to_domain(self, record: PropertyRecord) -> PropertyData:
        address = Address(line1=record.line1, city=record.city, state=record.state, zip=record.zip)
        sources: List[ApiSource] = []
        for source_record in list(record.sources):
            try:
                sources.append(ApiSource(source_record.source))
            except ValueError:
                logger.debug("Ignoring unknown source '%s' while hydrating property", source_record.source)
                continue

        return PropertyData(
            address=address,
            beds=record.beds,
            baths=record.baths,
            sqft=record.sqft,
            lot_sqft=record.lot_sqft,
            year_built=record.year_built,
            market_value_estimate=record.market_value_estimate,
            rent_estimate=record.rent_estimate,
            annual_taxes=record.annual_taxes,
            closing_cost_estimate=record.closing_cost_estimate,
            meta=dict(record.meta or {}),
            sources=sources,
        )


def get_repository() -> PropertyRepository:
    global _repository
    if _repository is None:
        _repository = PropertyRepository()
    return _repository


def configure(database_url: str) -> None:
    """Explicitly configure the persistence layer (useful for tests)."""

    global _repository
    init_engine(database_url)
    _repository = PropertyRepository(get_session_factory())
