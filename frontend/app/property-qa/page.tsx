"use client";

import { useMemo, useState } from "react";
import { AddressAutocomplete } from "../../components/AddressAutocomplete";
import JsonCodeBlock from "../../components/JsonCodeBlock";
import { runPropertyQA } from "../../lib/api";
import type { PropertyQAResponse } from "../../types";

const defaultQuestion = "Is this property exposed to flood risk or other hazards?";

function buildAddressLine(parts: {
  line1?: string | null;
  city?: string | null;
  state?: string | null;
  zip?: string | null;
}) {
  const { line1, city, state, zip } = parts;
  const pieces = [line1, city, [state, zip].filter(Boolean).join(" ")].filter(Boolean);
  return pieces.join(", ").trim();
}

export default function PropertyQA() {
  const [question, setQuestion] = useState(defaultQuestion);
  const [addressLine, setAddressLine] = useState("");
  const [addressSearch, setAddressSearch] = useState("");
  const [yearBuilt, setYearBuilt] = useState("");
  const [occupancy, setOccupancy] = useState("");
  const [knownHazards, setKnownHazards] = useState("");

  const [result, setResult] = useState<PropertyQAResponse | null>(null);
  const [lastPayload, setLastPayload] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const payloadPreview = useMemo(
    () => ({
      question,
      address: addressLine || undefined,
      year_built: yearBuilt ? Number(yearBuilt) : undefined,
      occupancy: occupancy || undefined,
      known_hazards: knownHazards || undefined,
    }),
    [question, addressLine, yearBuilt, occupancy, knownHazards]
  );

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsLoading(true);
    setResult(null);

    if (!question.trim()) {
      setError("Please enter a question about the property.");
      setIsLoading(false);
      return;
    }

    const payload = {
      question: question.trim(),
      address: addressLine.trim() || undefined,
      year_built: yearBuilt ? Number(yearBuilt) : undefined,
      occupancy: occupancy.trim() || undefined,
      known_hazards: knownHazards.trim() || undefined,
    };

    try {
      const response = await runPropertyQA(payload);
      setResult(response);
      setLastPayload(payload as Record<string, unknown>);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsLoading(false);
    }
  }

  function handleAddressResolved(
    address: { line1: string; city: string; state: string; zip: string },
    suggestion: { description: string }
  ) {
    setAddressLine(buildAddressLine(address));
    setAddressSearch(suggestion.description || buildAddressLine(address));
  }

  function applySample() {
    setQuestion("Could heavy rain cause issues for this 1940s river-adjacent home?");
    setAddressLine("123 River St, Riverside, CA 92501");
    setAddressSearch("123 River St, Riverside, CA 92501");
    setYearBuilt("1940");
    setOccupancy("Residential");
    setKnownHazards("Near river; noted seasonal flooding");
  }

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-10 sm:px-6 lg:px-8">
      <div className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
        <section className="glass-card relative border border-border/60 shadow-lg shadow-primary/5">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-accent/5" aria-hidden />
          <div className="relative flex flex-col gap-6 p-6 sm:p-8">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-wide text-text-muted">ML Assistant</p>
                <h1 className="text-2xl font-semibold text-text">Property Q&amp;A</h1>
                <p className="mt-1 text-sm text-text-muted">
                  Ask about flood risk, building age implications, or general hazard context for a property.
                  The backend uses the new /api/ml/property_qa endpoint with local heuristics or your configured
                  remote model.
                </p>
              </div>
              <button
                type="button"
                onClick={applySample}
                className="primary-button whitespace-nowrap"
                aria-label="Fill sample inputs"
              >
                Load sample
              </button>
            </div>

            <form className="grid gap-6" onSubmit={handleSubmit}>
              <div className="grid gap-3">
                <label className="field-label">Question</label>
                <textarea
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  className="field-input min-h-[120px] resize-vertical"
                  placeholder="What risks should I consider for this property?"
                />
              </div>

              <div className="grid gap-4 lg:grid-cols-2">
                <div className="grid gap-3">
                  <label className="field-label">Address (optional)</label>
                  <AddressAutocomplete
                    query={addressSearch}
                    onQueryChange={setAddressSearch}
                    onAddressResolved={handleAddressResolved}
                  />
                  <input
                    value={addressLine}
                    onChange={(e) => setAddressLine(e.target.value)}
                    placeholder="123 Main St, City, ST 12345"
                    className="field-input"
                  />
                </div>

                <div className="grid gap-3">
                  <label className="field-label">Context (optional)</label>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <input
                      type="number"
                      inputMode="numeric"
                      pattern="[0-9]*"
                      value={yearBuilt}
                      onChange={(e) => setYearBuilt(e.target.value)}
                      placeholder="Year built"
                      className="field-input"
                    />
                    <input
                      value={occupancy}
                      onChange={(e) => setOccupancy(e.target.value)}
                      placeholder="Occupancy (e.g., Residential)"
                      className="field-input"
                    />
                  </div>
                  <textarea
                    value={knownHazards}
                    onChange={(e) => setKnownHazards(e.target.value)}
                    placeholder="Known hazards (e.g., near river, wildfire zone)"
                    className="field-input min-h-[80px] resize-vertical"
                  />
                </div>
              </div>

              {error && <p className="text-sm text-rose-500">{error}</p>}

              <div className="flex items-center gap-3">
                <button type="submit" className="primary-button" disabled={isLoading}>
                  {isLoading ? "Calling API..." : "Ask the assistant"}
                </button>
                <p className="text-sm text-text-muted">
                  Responses use the backend risk heuristic when remote inference is unavailable.
                </p>
              </div>
            </form>
          </div>
        </section>

        <aside className="glass-card border border-border/60 p-6 sm:p-8 shadow-lg shadow-primary/5">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-wide text-text-muted">Response</p>
              <h2 className="text-lg font-semibold text-text">Answer &amp; Risk</h2>
            </div>
            {result?.risk_score && (
              <span className="chip chip-active capitalize">Risk: {result.risk_score}</span>
            )}
          </div>

          {result ? (
            <div className="grid gap-4">
              <div className="rounded-xl border border-border bg-surface-alt/60 p-4 shadow-subtle">
                <p className="text-sm leading-relaxed text-text">{result.answer}</p>
              </div>

              {result.debug && (
                <div className="grid gap-2">
                  <p className="text-sm font-medium text-text">Debug details</p>
                  <JsonCodeBlock data={result.debug} maxHeight={220} />
                </div>
              )}
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-border bg-surface-alt/50 p-6 text-sm text-text-muted">
              Run a query to see the assistant&apos;s response and risk score. We&apos;ll show any backend debug metadata here, too.
            </div>
          )}
        </aside>
      </div>

      <section className="glass-card border border-border/60 p-6 sm:p-8 shadow-lg shadow-primary/5">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-text-muted">Request preview</p>
            <h3 className="text-lg font-semibold text-text">Payload sent to /api/ml/property_qa</h3>
          </div>
          {lastPayload && <span className="chip">Last call succeeded</span>}
        </div>
        <p className="mt-1 text-sm text-text-muted">
          This mirrors exactly what the frontend sends to the new backend endpoint. Use it to debug or plug in a remote model.
        </p>
        <div className="mt-4">
          <JsonCodeBlock data={lastPayload ?? payloadPreview} maxHeight={320} />
        </div>
      </section>
    </div>
  );
}
