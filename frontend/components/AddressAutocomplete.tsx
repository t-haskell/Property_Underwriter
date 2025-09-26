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
        const results = await suggestPlaces(current);
        if (!ignore) {
          setSuggestions(results);
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
          {suggestions.map((suggestion) => (
            <button
              key={suggestion.place_id}
              type="button"
              onClick={() => handleSuggestionClick(suggestion)}
              style={{
                textAlign: "left",
                padding: "0.75rem 0.85rem",
                borderRadius: 8,
                border: "1px solid #cbd5e1",
                background: "#fff",
                cursor: "pointer",
              }}
            >
              {suggestion.description}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
