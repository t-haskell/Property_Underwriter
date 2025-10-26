'use client';

import { Dispatch, FormEvent, SetStateAction, useEffect, useMemo, useState } from "react";
import { AddressAutocomplete } from "../components/AddressAutocomplete";
import JsonCodeBlock from "../components/JsonCodeBlock";
import {
  fetchProperty,
  runFlipAnalysis,
  runRentalAnalysis,
} from "../lib/api";
import type {
  Address,
  FlipResult,
  PropertyData,
  RentalResult,
  Suggestion,
} from "../types";
import type { FlipAssumptions, RentalAssumptions } from "../types";

const MERGED_PAYLOAD_KEY = "__merged_property__";

const rentalDefaults = {
  purchasePrice: 350_000,
  downPaymentPct: 20,
  interestRatePct: 6.5,
  loanTermYears: 30,
  vacancyPct: 5,
  managementPct: 8,
  maintenanceReserve: 1_200,
  capexReserve: 1_200,
  insurance: 1_200,
  hoa: 0,
  holdYears: 5,
  targetCapRatePct: 0,
  targetIrrPct: 0,
};

const flipDefaults = {
  candidatePrice: 250_000,
  downPaymentPct: 20,
  interestRatePct: 6.5,
  loanTermYears: 30,
  renovationBudget: 60_000,
  holdMonths: 6,
  targetMarginPct: 10,
  closingBuyPct: 2,
  closingSellPct: 6,
  arvOverride: 0,
};

type AnalysisType = "rental" | "flip";

export default function Home() {
  const [searchQuery, setSearchQuery] = useState("");
  const [address, setAddress] = useState<Address>({
    line1: "",
    city: "",
    state: "",
    zip: "",
  });

  const [analysisType, setAnalysisType] = useState<AnalysisType>("rental");
  const [property, setProperty] = useState<PropertyData | null>(null);

  const [rentalForm, setRentalForm] = useState({ ...rentalDefaults });
  const [flipForm, setFlipForm] = useState({ ...flipDefaults });

  const [rentalResult, setRentalResult] = useState<RentalResult | null>(null);
  const [flipResult, setFlipResult] = useState<FlipResult | null>(null);

  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isFetchingProperty, setIsFetchingProperty] = useState(false);
  const [isRunningAnalysis, setIsRunningAnalysis] = useState(false);
  const [selectedRawKey, setSelectedRawKey] = useState<string>(MERGED_PAYLOAD_KEY);

  const propertyIdentity = useMemo(() => {
    if (!property) {
      return null;
    }
    const addressKey = `${property.address.line1}|${property.address.city}|${property.address.state}|${property.address.zip}`;
    const metaKey = property.meta ? Object.keys(property.meta).sort().join("|") : "";
    return `${addressKey}|${metaKey}`;
  }, [property]);

  function updateAddressField(field: keyof Address, value: string) {
    setAddress((prev) => ({ ...prev, [field]: value }));
  }

  function handleSuggestion(addressResolved: Address, suggestion: Suggestion) {
    setSearchQuery(suggestion.description);
    setAddress(addressResolved);
  }

  async function handleFetchProperty(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setStatus(null);
    setRentalResult(null);
    setFlipResult(null);

    if (!address.line1 || !address.city || !address.state || !address.zip) {
      setError("Please complete the address before fetching property data.");
      return;
    }

    setIsFetchingProperty(true);
    try {
      const propertyData = await fetchProperty(address);
      setProperty(propertyData);
      setStatus("Property data loaded.");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsFetchingProperty(false);
    }
  }

  const propertySummary = useMemo(() => {
    if (!property) {
      return null;
    }
    const entries: Array<[string, string | number]> = [
      ["Address", `${property.address.line1}, ${property.address.city}, ${property.address.state} ${property.address.zip}`],
    ];

    if (property.market_value_estimate) entries.push(["Market Value", formatCurrency(property.market_value_estimate)]);
    if (property.rent_estimate) entries.push(["Rent Estimate", formatCurrency(property.rent_estimate)]);
    if (property.annual_taxes) entries.push(["Annual Taxes", formatCurrency(property.annual_taxes)]);
    if (property.beds) entries.push(["Beds", property.beds]);
    if (property.baths) entries.push(["Baths", property.baths]);
    if (property.sqft) entries.push(["Sq Ft", property.sqft]);
    if (property.lot_sqft) entries.push(["Lot Sq Ft", property.lot_sqft]);
    if (property.year_built) entries.push(["Year Built", property.year_built]);

    return entries;
  }, [property]);

  // Prefer full provider raw JSON (e.g., rentcast_raw) if present
  const rawEntries = useMemo(() => {
    if (!property?.meta) {
      return [] as Array<{ key: string; label: string; value: unknown }>;
    }

    const formatLabel = (key: string) => {
      const cleaned = key.replace(/_raw$/i, "");
      if (!cleaned) return key;
      return cleaned
        .split(/[_-]/)
        .filter(Boolean)
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(" ");
    };

    const entries = Object.entries(property.meta)
      .filter(([key, value]) => key.toLowerCase().endsWith("_raw") && typeof value === "string")
      .map(([key, value]) => {
        let parsed: unknown = value;
        try {
          parsed = JSON.parse(value as string);
        } catch {
          parsed = value;
        }
        return { key, label: formatLabel(key), value: parsed };
      });

    return entries.sort((a, b) => a.label.localeCompare(b.label));
  }, [property]);

  useEffect(() => {
    setSelectedRawKey(MERGED_PAYLOAD_KEY);
  }, [propertyIdentity]);

  useEffect(() => {
    setSelectedRawKey((current) => {
      if (!property || rawEntries.length === 0) {
        return MERGED_PAYLOAD_KEY;
      }

      if (current === MERGED_PAYLOAD_KEY) {
        return MERGED_PAYLOAD_KEY;
      }

      if (rawEntries.some((entry) => entry.key === current)) {
        return current;
      }

      return rawEntries[0]?.key ?? MERGED_PAYLOAD_KEY;
    });
  }, [property, rawEntries]);

  const propertyRawForViewer = useMemo(() => {
    if (!property) return null;
    if (selectedRawKey === MERGED_PAYLOAD_KEY || rawEntries.length === 0) {
      return property;
    }

    const match = rawEntries.find((entry) => entry.key === selectedRawKey);
    return match?.value ?? property;
  }, [property, rawEntries, selectedRawKey]);

  async function handleRentalSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setStatus(null);
    setRentalResult(null);

    if (!property) {
      setError("Load property data before running the rental analysis.");
      return;
    }

    setIsRunningAnalysis(true);
    try {
      const assumptions: RentalAssumptions = {
        down_payment_pct: rentalForm.downPaymentPct,
        interest_rate_annual: rentalForm.interestRatePct / 100,
        loan_term_years: rentalForm.loanTermYears,
        vacancy_rate_pct: rentalForm.vacancyPct,
        maintenance_reserve_annual: rentalForm.maintenanceReserve,
        capex_reserve_annual: rentalForm.capexReserve,
        insurance_annual: rentalForm.insurance,
        hoa_annual: rentalForm.hoa,
        property_mgmt_pct: rentalForm.managementPct,
        hold_period_years: rentalForm.holdYears,
        target_cap_rate_pct: rentalForm.targetCapRatePct || undefined,
        target_irr_pct: rentalForm.targetIrrPct || undefined,
      };

      const result = await runRentalAnalysis(property, assumptions, rentalForm.purchasePrice);
      setRentalResult(result);
      setStatus("Rental analysis complete.");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsRunningAnalysis(false);
    }
  }

  async function handleFlipSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setStatus(null);
    setFlipResult(null);

    if (!property) {
      setError("Load property data before running the flip analysis.");
      return;
    }

    setIsRunningAnalysis(true);
    try {
      const assumptions: FlipAssumptions = {
        down_payment_pct: flipForm.downPaymentPct,
        interest_rate_annual: flipForm.interestRatePct / 100,
        loan_term_years: flipForm.loanTermYears,
        renovation_budget: flipForm.renovationBudget,
        hold_time_months: flipForm.holdMonths,
        target_margin_pct: flipForm.targetMarginPct / 100,
        closing_pct_buy: flipForm.closingBuyPct / 100,
        closing_pct_sell: flipForm.closingSellPct / 100,
        arv_override: flipForm.arvOverride || undefined,
      };

      const result = await runFlipAnalysis(property, assumptions, flipForm.candidatePrice);
      setFlipResult(result);
      setStatus("Flip analysis complete.");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsRunningAnalysis(false);
    }
  }

  return (
    <main style={{ maxWidth: 1200, margin: "0 auto", padding: "2rem 1.5rem" }}>
      <header style={{ marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "2.25rem", marginBottom: "0.5rem" }}>
          🏠 Property Underwriter
        </h1>
        <p style={{ maxWidth: 720, lineHeight: 1.6 }}>
          Fetch property data, compare rental and flip assumptions, and review the underwriting outputs in a modern web experience.
        </p>
      </header>

      <section
        style={{
          background: "#fff",
          padding: "1.5rem",
          borderRadius: 16,
          boxShadow: "0 10px 30px rgba(15, 23, 42, 0.05)",
          marginBottom: "1.5rem",
        }}
      >
        <h2 style={{ marginTop: 0 }}>Property Address</h2>

        <div style={{ display: "grid", gap: "1.5rem" }}>
          <AddressAutocomplete
            query={searchQuery}
            onQueryChange={setSearchQuery}
            onAddressResolved={handleSuggestion}
          />

          <div style={{ display: "grid", gap: "0.75rem" }}>
            <div>
              <label className="field-label" htmlFor="line1">
                Street Address
              </label>
              <input
                id="line1"
                value={address.line1}
                onChange={(event) => updateAddressField("line1", event.target.value)}
                placeholder="123 Main St"
                className="field-input"
              />
            </div>
            <div style={{ display: "grid", gap: "0.75rem", gridTemplateColumns: "2fr 1fr" }}>
              <div>
                <label className="field-label" htmlFor="city">
                  City
                </label>
                <input
                  id="city"
                  value={address.city}
                  onChange={(event) => updateAddressField("city", event.target.value)}
                  placeholder="Boston"
                  className="field-input"
                />
              </div>
              <div>
                <label className="field-label" htmlFor="state">
                  State
                </label>
                <input
                  id="state"
                  value={address.state}
                  onChange={(event) => updateAddressField("state", event.target.value.toUpperCase())}
                  placeholder="MA"
                  className="field-input"
                  maxLength={2}
                />
              </div>
            </div>
            <div>
              <label className="field-label" htmlFor="zip">
                ZIP / Postal Code
              </label>
              <input
                id="zip"
                value={address.zip}
                onChange={(event) => updateAddressField("zip", event.target.value)}
                placeholder="02129"
                className="field-input"
              />
            </div>
          </div>

          <form onSubmit={handleFetchProperty}>
            <button className="primary-button" type="submit" disabled={isFetchingProperty}>
              {isFetchingProperty ? "Fetching..." : "Fetch Property Data"}
            </button>
          </form>
        </div>
      </section>

      <section
        style={{
          background: "#fff",
          padding: "1.5rem",
          borderRadius: 16,
          boxShadow: "0 10px 30px rgba(15, 23, 42, 0.05)",
          marginBottom: "1.5rem",
        }}
      >
        <h2 style={{ marginTop: 0 }}>Analysis Type</h2>
        <div style={{ display: "flex", gap: "1rem" }}>
          <button
            type="button"
            className={analysisType === "rental" ? "chip chip-active" : "chip"}
            onClick={() => setAnalysisType("rental")}
          >
            Rental Analysis
          </button>
          <button
            type="button"
            className={analysisType === "flip" ? "chip chip-active" : "chip"}
            onClick={() => setAnalysisType("flip")}
          >
            Flip Analysis
          </button>
        </div>
      </section>

      {property && (
        <section
          style={{
            background: "#fff",
            padding: "1.5rem",
            borderRadius: 16,
            boxShadow: "0 10px 30px rgba(15, 23, 42, 0.05)",
            marginBottom: "1.5rem",
          }}
        >
          <h2 style={{ marginTop: 0 }}>Property Snapshot</h2>
          <div style={{ display: "grid", gap: "0.6rem" }}>
            {propertySummary?.map(([label, value]) => (
              <div key={label} style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ fontWeight: 500 }}>{label}</span>
                <span>{value}</span>
              </div>
            ))}
          </div>
          <details style={{ marginTop: "1rem" }}>
            <summary style={{ cursor: "pointer", userSelect: "none" }}>
              View ALL property data scraped
            </summary>
            <div style={{ marginTop: "0.75rem" }}>
              {rawEntries.length > 0 && (
                <div
                  style={{
                    marginBottom: "0.75rem",
                    display: "flex",
                    gap: "0.5rem",
                    flexWrap: "wrap",
                    alignItems: "center",
                  }}
                >
                  <label htmlFor="provider-payload-select" style={{ fontWeight: 500 }}>
                    Provider response
                  </label>
                  <select
                    id="provider-payload-select"
                    value={selectedRawKey}
                    onChange={(event) => setSelectedRawKey(event.target.value)}
                    style={{ padding: "0.4rem 0.6rem", borderRadius: 8, border: "1px solid #CBD5F5" }}
                  >
                    <option value={MERGED_PAYLOAD_KEY}>Merged property snapshot</option>
                    {rawEntries.map((entry) => (
                      <option key={entry.key} value={entry.key}>
                        {entry.label} JSON
                      </option>
                    ))}
                  </select>
                </div>
              )}
              <JsonCodeBlock data={propertyRawForViewer ?? property} />
            </div>
          </details>
        </section>
      )}

      <section
        style={{
          background: "#fff",
          padding: "1.5rem",
          borderRadius: 16,
          boxShadow: "0 10px 30px rgba(15, 23, 42, 0.05)",
          marginBottom: "1.5rem",
        }}
      >
        {analysisType === "rental" ? (
          <RentalForm
            formState={rentalForm}
            setFormState={setRentalForm}
            onSubmit={handleRentalSubmit}
            disabled={isRunningAnalysis}
          />
        ) : (
          <FlipForm
            formState={flipForm}
            setFormState={setFlipForm}
            onSubmit={handleFlipSubmit}
            disabled={isRunningAnalysis}
          />
        )}
      </section>

      {(rentalResult || flipResult) && (
        <section
          style={{
            background: "#fff",
            padding: "1.5rem",
            borderRadius: 16,
            boxShadow: "0 10px 30px rgba(15, 23, 42, 0.05)",
            marginBottom: "1.5rem",
          }}
        >
          <h2 style={{ marginTop: 0 }}>Results</h2>
          <div style={{ display: "grid", gap: "0.75rem" }}>
            {rentalResult && (
              <ResultsCard
                title="Rental Analysis"
                entries={[
                  ["Net Operating Income", formatCurrency(rentalResult.noi_annual)],
                  ["Annual Debt Service", formatCurrency(rentalResult.annual_debt_service)],
                  ["Annual Cash Flow", formatCurrency(rentalResult.cash_flow_annual)],
                  ["Cap Rate", `${rentalResult.cap_rate_pct.toFixed(2)}%`],
                  ["IRR", rentalResult.irr_pct ? `${rentalResult.irr_pct.toFixed(2)}%` : "—"],
                  [
                    "Suggested Purchase Price",
                    rentalResult.suggested_purchase_price
                      ? formatCurrency(rentalResult.suggested_purchase_price)
                      : "—",
                  ],
                ]}
              />
            )}
            {flipResult && (
              <ResultsCard
                title="Flip Analysis"
                entries={[
                  ["After Repair Value", formatCurrency(flipResult.arv)],
                  ["Total Costs", formatCurrency(flipResult.total_costs)],
                  ["Suggested Purchase Price", formatCurrency(flipResult.suggested_purchase_price)],
                  ["Projected Profit", formatCurrency(flipResult.projected_profit)],
                  ["Margin", `${flipResult.margin_pct.toFixed(2)}%`],
                ]}
              />
            )}
          </div>
        </section>
      )}

      {(status || error) && (
        <section style={{ marginBottom: "2rem" }}>
          {status && <p style={{ color: "#047857" }}>{status}</p>}
          {error && <p style={{ color: "#b91c1c" }}>{error}</p>}
        </section>
      )}
    </main>
  );
}

interface RentalFormProps {
  formState: typeof rentalDefaults;
  setFormState: Dispatch<SetStateAction<typeof rentalDefaults>>;
  onSubmit: (event: FormEvent) => void;
  disabled: boolean;
}

function RentalForm({ formState, setFormState, onSubmit, disabled }: RentalFormProps) {
  function update(field: keyof typeof rentalDefaults, value: number) {
    setFormState({ ...formState, [field]: value });
  }

  return (
    <form onSubmit={onSubmit} style={{ display: "grid", gap: "1rem" }}>
      <h2 style={{ marginTop: 0 }}>Rental Assumptions</h2>
      <div className="grid-two">
        <NumberField
          label="Purchase Price ($)"
          value={formState.purchasePrice}
          onChange={(v) => update("purchasePrice", v)}
        />
        <NumberField
          label="Down Payment (%)"
          value={formState.downPaymentPct}
          onChange={(v) => update("downPaymentPct", v)}
          min={0}
          max={100}
        />
        <NumberField
          label="Interest Rate (%)"
          value={formState.interestRatePct}
          onChange={(v) => update("interestRatePct", v)}
          step={0.1}
        />
        <NumberField
          label="Loan Term (years)"
          value={formState.loanTermYears}
          onChange={(v) => update("loanTermYears", v)}
          min={1}
        />
        <NumberField
          label="Vacancy (%)"
          value={formState.vacancyPct}
          onChange={(v) => update("vacancyPct", v)}
          step={0.5}
        />
        <NumberField
          label="Management (%)"
          value={formState.managementPct}
          onChange={(v) => update("managementPct", v)}
          step={0.5}
        />
        <NumberField
          label="Maintenance Reserve ($)"
          value={formState.maintenanceReserve}
          onChange={(v) => update("maintenanceReserve", v)}
          step={100}
        />
        <NumberField
          label="CapEx Reserve ($)"
          value={formState.capexReserve}
          onChange={(v) => update("capexReserve", v)}
          step={100}
        />
        <NumberField
          label="Insurance ($)"
          value={formState.insurance}
          onChange={(v) => update("insurance", v)}
          step={100}
        />
        <NumberField
          label="HOA ($)"
          value={formState.hoa}
          onChange={(v) => update("hoa", v)}
          step={100}
        />
        <NumberField
          label="Hold Period (years)"
          value={formState.holdYears}
          onChange={(v) => update("holdYears", v)}
          min={1}
        />
        <NumberField
          label="Target Cap Rate (%)"
          value={formState.targetCapRatePct}
          onChange={(v) => update("targetCapRatePct", v)}
          step={0.5}
        />
        <NumberField
          label="Target IRR (%)"
          value={formState.targetIrrPct}
          onChange={(v) => update("targetIrrPct", v)}
          step={0.5}
        />
      </div>
      <button className="primary-button" type="submit" disabled={disabled}>
        {disabled ? "Analyzing..." : "Run Rental Analysis"}
      </button>
    </form>
  );
}

interface FlipFormProps {
  formState: typeof flipDefaults;
  setFormState: Dispatch<SetStateAction<typeof flipDefaults>>;
  onSubmit: (event: FormEvent) => void;
  disabled: boolean;
}

function FlipForm({ formState, setFormState, onSubmit, disabled }: FlipFormProps) {
  function update(field: keyof typeof flipDefaults, value: number) {
    setFormState({ ...formState, [field]: value });
  }

  return (
    <form onSubmit={onSubmit} style={{ display: "grid", gap: "1rem" }}>
      <h2 style={{ marginTop: 0 }}>Flip Assumptions</h2>
      <div className="grid-two">
        <NumberField
          label="Candidate Purchase Price ($)"
          value={formState.candidatePrice}
          onChange={(v) => update("candidatePrice", v)}
        />
        <NumberField
          label="Down Payment (%)"
          value={formState.downPaymentPct}
          onChange={(v) => update("downPaymentPct", v)}
        />
        <NumberField
          label="Interest Rate (%)"
          value={formState.interestRatePct}
          onChange={(v) => update("interestRatePct", v)}
          step={0.1}
        />
        <NumberField
          label="Loan Term (years)"
          value={formState.loanTermYears}
          onChange={(v) => update("loanTermYears", v)}
          min={1}
        />
        <NumberField
          label="Renovation Budget ($)"
          value={formState.renovationBudget}
          onChange={(v) => update("renovationBudget", v)}
          step={1000}
        />
        <NumberField
          label="Hold Time (months)"
          value={formState.holdMonths}
          onChange={(v) => update("holdMonths", v)}
          min={1}
        />
        <NumberField
          label="Target Margin (%)"
          value={formState.targetMarginPct}
          onChange={(v) => update("targetMarginPct", v)}
          step={0.5}
        />
        <NumberField
          label="Closing Costs on Buy (%)"
          value={formState.closingBuyPct}
          onChange={(v) => update("closingBuyPct", v)}
          step={0.1}
        />
        <NumberField
          label="Closing Costs on Sell (%)"
          value={formState.closingSellPct}
          onChange={(v) => update("closingSellPct", v)}
          step={0.1}
        />
        <NumberField
          label="ARV Override ($)"
          value={formState.arvOverride}
          onChange={(v) => update("arvOverride", v)}
          step={5000}
        />
      </div>
      <button className="primary-button" type="submit" disabled={disabled}>
        {disabled ? "Analyzing..." : "Run Flip Analysis"}
      </button>
    </form>
  );
}

interface NumberFieldProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
}

function NumberField({ label, value, onChange, min, max, step }: NumberFieldProps) {
  return (
    <label className="field-group">
      <span className="field-label">{label}</span>
      <input
        type="number"
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        min={min}
        max={max}
        step={step}
        className="field-input"
      />
    </label>
  );
}

interface ResultsCardProps {
  title: string;
  entries: Array<[string, string]>;
}

function ResultsCard({ title, entries }: ResultsCardProps) {
  return (
    <div
      style={{
        border: "1px solid #e2e8f0",
        borderRadius: 16,
        padding: "1rem",
        background: "#f8fafc",
      }}
    >
      <h3 style={{ marginTop: 0 }}>{title}</h3>
      <div style={{ display: "grid", gap: "0.5rem" }}>
        {entries.map(([label, value]) => (
          <div key={label} style={{ display: "flex", justifyContent: "space-between" }}>
            <span>{label}</span>
            <span style={{ fontWeight: 600 }}>{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}
