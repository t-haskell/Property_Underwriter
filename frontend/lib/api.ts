import type {
  Address,
  FlipAssumptions,
  FlipResult,
  PropertyData,
  RentalAssumptions,
  RentalResult,
  Suggestion,
} from "../types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.trim()?.replace(/\/+$/, "") ?? "http://127.0.0.1:8000";

function buildApiUrl(path: string): string {
  if (!API_BASE_URL) {
    return path;
  }
  return `${API_BASE_URL}${path}`;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function suggestPlaces(query: string, limit: number = 5): Promise<Suggestion[]> {
  const searchParams = new URLSearchParams({ query, limit: limit.toString() });
  const url = `${buildApiUrl("/api/places/suggest")}?${searchParams.toString()}`;
  const response = await fetch(url);
  const data = await handleResponse<{ suggestions: Suggestion[] }>(response);
  return data.suggestions;
}

export async function resolveSuggestion(suggestion: Suggestion): Promise<Address | null> {
  const response = await fetch(buildApiUrl("/api/places/resolve"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ suggestion }),
  });
  const data = await handleResponse<{ address: Address | null }>(response);
  return data.address;
}

export async function fetchProperty(address: Address): Promise<PropertyData> {
  const response = await fetch(buildApiUrl("/api/property/fetch"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ address }),
  });
  return handleResponse<PropertyData>(response);
}

export async function runRentalAnalysis(
  property: PropertyData,
  assumptions: RentalAssumptions,
  purchase_price: number
): Promise<RentalResult> {
  const response = await fetch(buildApiUrl("/api/analyze/rental"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ property, assumptions, purchase_price }),
  });
  return handleResponse<RentalResult>(response);
}

export async function runFlipAnalysis(
  property: PropertyData,
  assumptions: FlipAssumptions,
  candidate_price: number
): Promise<FlipResult> {
  const response = await fetch(buildApiUrl("/api/analyze/flip"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ property, assumptions, candidate_price }),
  });
  return handleResponse<FlipResult>(response);
}

