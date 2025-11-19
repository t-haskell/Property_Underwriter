'use client';

import { Dispatch, FormEvent, SetStateAction, useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
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
    <main className="min-h-screen p-4 sm:p-8 lg:p-12 max-w-7xl mx-auto">
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-10 text-center"
      >
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-4 bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
          Property Underwriter
        </h1>
        <p className="text-lg text-text-muted max-w-2xl mx-auto">
          Professional-grade real estate analysis powered by multi-source data aggregation.
        </p>
      </motion.header>

      <div className="grid lg:grid-cols-12 gap-8">
        <div className="lg:col-span-5 space-y-6">
          {/* Address Section */}
          <motion.section
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="glass-card p-6"
          >
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <span className="text-2xl">📍</span> Property Address
            </h2>

            <div className="space-y-4">
              <AddressAutocomplete
                query={searchQuery}
                onQueryChange={setSearchQuery}
                onAddressResolved={handleSuggestion}
              />

              <div className="space-y-3">
                <div>
                  <label className="field-label" htmlFor="line1">Street Address</label>
                  <input
                    id="line1"
                    value={address.line1}
                    onChange={(e) => updateAddressField("line1", e.target.value)}
                    placeholder="123 Main St"
                    className="field-input"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="field-label" htmlFor="city">City</label>
                    <input
                      id="city"
                      value={address.city}
                      onChange={(e) => updateAddressField("city", e.target.value)}
                      placeholder="Boston"
                      className="field-input"
                    />
                  </div>
                  <div>
                    <label className="field-label" htmlFor="state">State</label>
                    <input
                      id="state"
                      value={address.state}
                      onChange={(e) => updateAddressField("state", e.target.value.toUpperCase())}
                      placeholder="MA"
                      className="field-input"
                      maxLength={2}
                    />
                  </div>
                </div>
                <div>
                  <label className="field-label" htmlFor="zip">ZIP Code</label>
                  <input
                    id="zip"
                    value={address.zip}
                    onChange={(e) => updateAddressField("zip", e.target.value)}
                    placeholder="02129"
                    className="field-input"
                  />
                </div>
              </div>

              <button
                onClick={handleFetchProperty}
                disabled={isFetchingProperty}
                className="primary-button w-full mt-2"
              >
                {isFetchingProperty ? (
                  <>
                    <span className="animate-spin">↻</span> Fetching Data...
                  </>
                ) : (
                  "Fetch Property Data"
                )}
              </button>
            </div>
          </motion.section>

          {/* Analysis Type Toggle */}
          <motion.section
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-card p-6"
          >
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <span className="text-2xl">📊</span> Analysis Strategy
            </h2>
            <div className="flex p-1 bg-surface-alt/50 rounded-xl border border-border/50 relative">
              <div className="absolute inset-1 bg-white rounded-lg shadow-sm transition-all duration-300"
                style={{
                  width: 'calc(50% - 0.5rem)',
                  left: analysisType === 'rental' ? '0.25rem' : 'calc(50% + 0.25rem)'
                }}
              />
              <button
                type="button"
                className={`flex-1 relative z-10 py-2 text-sm font-medium rounded-lg transition-colors duration-200 ${analysisType === "rental" ? "text-primary" : "text-text-muted hover:text-text"
                  }`}
                onClick={() => setAnalysisType("rental")}
              >
                Rental Strategy
              </button>
              <button
                type="button"
                className={`flex-1 relative z-10 py-2 text-sm font-medium rounded-lg transition-colors duration-200 ${analysisType === "flip" ? "text-primary" : "text-text-muted hover:text-text"
                  }`}
                onClick={() => setAnalysisType("flip")}
              >
                Flip Strategy
              </button>
            </div>
          </motion.section>

          {/* Assumptions Form */}
          <motion.section
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            className="glass-card p-6"
          >
            <AnimatePresence mode="wait">
              {analysisType === "rental" ? (
                <motion.div
                  key="rental-form"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                >
                  <RentalForm
                    formState={rentalForm}
                    setFormState={setRentalForm}
                    onSubmit={handleRentalSubmit}
                    disabled={isRunningAnalysis}
                  />
                </motion.div>
              ) : (
                <motion.div
                  key="flip-form"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                >
                  <FlipForm
                    formState={flipForm}
                    setFormState={setFlipForm}
                    onSubmit={handleFlipSubmit}
                    disabled={isRunningAnalysis}
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </motion.section>
        </div>

        <div className="lg:col-span-7 space-y-6">
          {/* Status Messages */}
          <AnimatePresence>
            {(status || error) && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className={`rounded-xl p-4 border ${error
                  ? "bg-red-50 border-red-200 text-red-700"
                  : "bg-emerald-50 border-emerald-200 text-emerald-700"
                  }`}
              >
                {status && <p className="flex items-center gap-2">✅ {status}</p>}
                {error && <p className="flex items-center gap-2">⚠️ {error}</p>}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Results Section */}
          <AnimatePresence>
            {(rentalResult || flipResult) && (
              <motion.section
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="glass-card p-8 border-primary/20 ring-1 ring-primary/10"
              >
                <h2 className="text-2xl font-bold mb-6 flex items-center gap-2 text-primary">
                  <span className="text-3xl">📈</span> Analysis Results
                </h2>
                <div className="grid gap-4">
                  {rentalResult && (
                    <ResultsCard
                      entries={[
                        ["Net Operating Income", formatCurrency(rentalResult.noi_annual)],
                        ["Annual Debt Service", formatCurrency(rentalResult.annual_debt_service)],
                        ["Annual Cash Flow", formatCurrency(rentalResult.cash_flow_annual)],
                        ["Cap Rate", `${rentalResult.cap_rate_pct.toFixed(2)}%`],
                        ["Cash on Cash Return", `${rentalResult.cash_on_cash_return_pct.toFixed(2)}%`],
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
              </motion.section>
            )}
          </AnimatePresence>

          {/* Property Snapshot */}
          {property && (
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-card p-6"
            >
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <span className="text-2xl">🏠</span> Property Snapshot
              </h2>
              <div className="grid sm:grid-cols-2 gap-4 mb-6">
                {propertySummary?.map(([label, value]) => (
                  <div key={label} className="flex justify-between items-center p-3 rounded-lg bg-surface-alt/30 border border-border/50">
                    <span className="text-sm text-text-muted">{label}</span>
                    <span className="font-semibold text-text">{value}</span>
                  </div>
                ))}
              </div>

              <details className="group">
                <summary className="flex items-center gap-2 cursor-pointer text-sm font-medium text-primary hover:text-primary-muted transition-colors select-none">
                  <span className="transition-transform group-open:rotate-90">▶</span>
                  View Raw Data Payload
                </summary>
                <div className="mt-4 pl-4 border-l-2 border-primary/10">
                  {rawEntries.length > 0 && (
                    <div className="mb-4 flex flex-wrap items-center gap-3">
                      <label htmlFor="provider-payload-select" className="text-sm font-medium text-text-muted">
                        Source:
                      </label>
                      <div className="relative">
                        <select
                          id="provider-payload-select"
                          value={selectedRawKey}
                          onChange={(event) => setSelectedRawKey(event.target.value)}
                          className="appearance-none bg-surface-alt border border-border rounded-lg py-1.5 pl-3 pr-8 text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none cursor-pointer"
                        >
                          <option value={MERGED_PAYLOAD_KEY}>Merged Snapshot</option>
                          {rawEntries.map((entry) => (
                            <option key={entry.key} value={entry.key}>
                              {entry.label}
                            </option>
                          ))}
                        </select>
                        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-text-muted">
                          <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" /></svg>
                        </div>
                      </div>
                    </div>
                  )}
                  <div className="rounded-lg overflow-hidden border border-border/50 shadow-inner bg-surface-alt/30">
                    <JsonCodeBlock data={propertyRawForViewer ?? property} />
                  </div>
                </div>
              </details>
            </motion.section>
          )}
        </div>
      </div>
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
    <form onSubmit={onSubmit} className="space-y-6">
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
          label="Maintenance ($/yr)"
          value={formState.maintenanceReserve}
          onChange={(v) => update("maintenanceReserve", v)}
          step={100}
        />
        <NumberField
          label="CapEx ($/yr)"
          value={formState.capexReserve}
          onChange={(v) => update("capexReserve", v)}
          step={100}
        />
        <NumberField
          label="Insurance ($/yr)"
          value={formState.insurance}
          onChange={(v) => update("insurance", v)}
          step={100}
        />
        <NumberField
          label="HOA ($/yr)"
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
      <button className="primary-button w-full" type="submit" disabled={disabled}>
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
    <form onSubmit={onSubmit} className="space-y-6">
      <div className="grid-two">
        <NumberField
          label="Candidate Price ($)"
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
          label="Reno Budget ($)"
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
          label="Buying Costs (%)"
          value={formState.closingBuyPct}
          onChange={(v) => update("closingBuyPct", v)}
          step={0.1}
        />
        <NumberField
          label="Selling Costs (%)"
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
      <button className="primary-button w-full" type="submit" disabled={disabled}>
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
  entries: Array<[string, string]>;
}

function ResultsCard({ entries }: ResultsCardProps) {
  return (
    <div className="grid gap-3">
      {entries.map(([label, value]) => (
        <div
          key={label}
          className="flex justify-between items-center p-4 rounded-xl bg-surface-alt/50 border border-border/50 hover:border-primary/30 transition-colors"
        >
          <span className="text-text-muted font-medium">{label}</span>
          <span className="text-lg font-bold text-primary">{value}</span>
        </div>
      ))}
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
