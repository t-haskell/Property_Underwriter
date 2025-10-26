import { useEffect, useState } from "react";
import { resolveSuggestion, suggestPlaces } from "../lib/api";
import type { Address, Suggestion } from "../types";
import { useDebouncedValue } from "../hooks/useDebouncedValue";

interface AddressAutocompleteProps {
  query: string;
  onQueryChange: (value: string) => void;
  onAddressResolved: (address: Address, suggestion: Suggestion) => void;
}

export function AddressAutocomplete({
  query,
  onQueryChange,
  onAddressResolved,
}: AddressAutocompleteProps) {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const debouncedQuery = useDebouncedValue(query, 250);

  useEffect(() => {
    let ignore = false;

    async function loadSuggestions(current: string) {
      if (current.trim().length < 2) {
        setSuggestions([]);
        return;
      }
      setIsLoading(true);
      setError(null);
      try {
        const results = await suggestPlaces(current, 10); // Request 10, get more after filtering
        // Keep only full addresses when the backend hasn't restarted yet
        const filtered = results.filter(isFullAddressClient);
        if (!ignore) {
          setSuggestions(filtered);
        }
      } catch (err) {
        if (!ignore) {
          setError((err as Error).message);
          setSuggestions([]);
        }
      } finally {
        if (!ignore) {
          setIsLoading(false);
        }
      }
    }

    loadSuggestions(debouncedQuery);

    return () => {
      ignore = true;
    };
  }, [debouncedQuery]);

  async function handleSuggestionClick(suggestion: Suggestion) {
    try {
      const address = await resolveSuggestion(suggestion);
      if (address) {
        onAddressResolved(address, suggestion);
      }
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div>
      <label style={{ display: "block", fontWeight: 600, marginBottom: 4 }}>
        Search Address
      </label>
      <input
        type="text"
        value={query}
        onChange={(event) => onQueryChange(event.target.value)}
        placeholder="Start typing an address..."
        style={{
          width: "100%",
          padding: "0.75rem 0.85rem",
          borderRadius: 8,
          border: "1px solid #cbd5e1",
          fontSize: "1rem",
        }}
      />
      {isLoading && <p style={{ marginTop: 8 }}>Searching...</p>}
      {error && (
        <p style={{ marginTop: 8, color: "#b91c1c" }}>
          {error}
        </p>
      )}
      {suggestions.length > 0 && (
        <div
          style={{
            marginTop: 12,
            display: "grid",
            gap: 8,
          }}
        >
          {suggestions.map((suggestion) => {
            const label = formatSuggestionLabel(suggestion);
            return (
            <button
              key={suggestion.place_id}
              type="button"
              onClick={() => handleSuggestionClick(suggestion)}
              style={{
                textAlign: "left",
                padding: "0.75rem 0.85rem",
                borderRadius: 8,
                border: "1px solid #cbd5e1",
                backgroundColor: "#ffffff",
                color: "#111827", // force dark text for readability across themes
                cursor: "pointer",
              }}
            >
              {label}
            </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

function formatSuggestionLabel(s: Suggestion): string {
  const street = (s.street ?? "").trim();
  const city = (s.city ?? "").trim();
  const state = (s.state ?? "").trim();
  const zip = (s.zip ?? "").trim();
  const locality = [state, zip].filter(Boolean).join(" ");
  const parts = [street, city, locality].filter(Boolean);
  return parts.length > 0 ? parts.join(", ") : (s.description || "").trim() || `Suggestion ${s.place_id ?? ""}`;
}

function isFullAddressClient(s: Suggestion): boolean {
  const street = (s.street ?? "").trim();
  const city = (s.city ?? "").trim();
  const state = (s.state ?? "").trim();
  // Make zip optional and remove the house number requirement
  if (!street || !city || !state) return false;
  return true; // Remove the /\d/.test(street) requirement
}
