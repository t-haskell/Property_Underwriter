export interface Address {
  line1: string;
  city: string;
  state: string;
  zip: string;
}

export interface PropertyData {
  address: Address;
  beds?: number | null;
  baths?: number | null;
  sqft?: number | null;
  lot_sqft?: number | null;
  year_built?: number | null;
  market_value_estimate?: number | null;
  rent_estimate?: number | null;
  annual_taxes?: number | null;
  closing_cost_estimate?: number | null;
  meta: Record<string, string>;
  sources: string[];
}

export interface Suggestion {
  description: string;
  place_id: string;
  // Optional structured fields (present in our API)
  street?: string | null;
  city?: string | null;
  state?: string | null; // two-letter code when available
  zip?: string | null;
  lat?: string | null;
  lon?: string | null;
}

export interface RentalAssumptions {
  down_payment_pct: number;
  interest_rate_annual: number;
  loan_term_years: number;
  vacancy_rate_pct: number;
  maintenance_reserve_annual: number;
  capex_reserve_annual: number;
  insurance_annual: number;
  hoa_annual: number;
  property_mgmt_pct: number;
  hold_period_years: number;
  closing_costs_pct?: number;
  target_cap_rate_pct?: number;
  target_irr_pct?: number;
}

export interface FlipAssumptions {
  down_payment_pct: number;
  interest_rate_annual: number;
  loan_term_years: number;
  renovation_budget: number;
  hold_time_months: number;
  target_margin_pct: number;
  closing_pct_buy: number;
  closing_pct_sell: number;
  arv_override?: number | null;
}

export interface RentalResult {
  noi_annual: number;
  annual_debt_service: number;
  cash_flow_annual: number;
  cap_rate_pct: number;
  irr_pct?: number | null;
  suggested_purchase_price?: number | null;
}

export interface FlipResult {
  arv: number;
  total_costs: number;
  suggested_purchase_price: number;
  projected_profit: number;
  margin_pct: number;
}
