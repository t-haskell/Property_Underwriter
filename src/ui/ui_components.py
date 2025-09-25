from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import streamlit as st

from ..core.models import Address, FlipAssumptions, RentalAssumptions
from ..services.nominatim_places import get_address_from_suggestion, get_place_suggestions
from ..utils.config import settings
from .autocomplete_component import enhanced_address_autocomplete, instant_address_autocomplete


RENTAL_DEFAULTS: Dict[str, float] = {
    "rental_purchase_price": 350000.0,
    "rental_down_payment_pct": 20.0,
    "rental_interest_rate_pct": 6.5,
    "rental_loan_term_years": 30,
    "rental_vacancy_pct": 5.0,
    "rental_management_pct": 8.0,
    "rental_maintenance_reserve": 1200.0,
    "rental_capex_reserve": 1200.0,
    "rental_insurance": 1200.0,
    "rental_hoa": 0.0,
    "rental_hold_years": 5,
    "rental_target_cap": 0.0,
    "rental_target_irr": 0.0,
}

FLIP_DEFAULTS: Dict[str, float] = {
    "flip_purchase_price": 250000.0,
    "flip_down_payment_pct": 20.0,
    "flip_interest_rate_pct": 6.5,
    "flip_loan_term_years": 30,
    "flip_renovation_budget": 60000.0,
    "flip_hold_months": 6,
    "flip_target_margin_pct": 10.0,
    "flip_closing_buy_pct": 2.0,
    "flip_closing_sell_pct": 6.0,
    "flip_arv_override": 0.0,
}

ADDRESS_DEFAULTS: Dict[str, str] = {
    "address_search_query": "",
    "address_suggestion_label": "",
    "selected_address_display": "",
    "manual_address_line1": "",
    "manual_address_city": "",
    "manual_address_state": "",
    "manual_address_zip": "",
}

def _ensure_address_state() -> None:
    for key, default in ADDRESS_DEFAULTS.items():
        st.session_state.setdefault(key, default)


def reset_rental_form_state() -> None:
    for key, default in RENTAL_DEFAULTS.items():
        st.session_state[key] = default


def reset_flip_form_state() -> None:
    for key, default in FLIP_DEFAULTS.items():
        st.session_state[key] = default


def _ensure_rental_defaults() -> None:
    for key, default in RENTAL_DEFAULTS.items():
        st.session_state.setdefault(key, default)


def _ensure_flip_defaults() -> None:
    for key, default in FLIP_DEFAULTS.items():
        st.session_state.setdefault(key, default)


def _format_selectbox_option(value: str) -> str:
    return value if value else "Select an address"


def address_input() -> Optional[Address]:
    _ensure_address_state()

    st.subheader("Property Address")
    
    # Use the enhanced autocomplete component
    selected_suggestion = enhanced_address_autocomplete(
        suggestions_func=get_place_suggestions,
        placeholder="Start typing an address...",
        max_suggestions=5,
        key="property_address_autocomplete"
    )
    
    # If user selected a suggestion, populate the manual fields
    if selected_suggestion:
        address = get_address_from_suggestion(selected_suggestion)
        if address:
            st.session_state.manual_address_line1 = address.line1
            st.session_state.manual_address_city = address.city
            st.session_state.manual_address_state = address.state
            st.session_state.manual_address_zip = address.zip
            st.success(f"✅ Address selected: {selected_suggestion.get('description', '')}")
    
    st.write("**Or enter manually:**")
    manual_line1 = st.text_input("Street Address", key="manual_address_line1")
    city_col, state_col = st.columns(2)
    manual_city = city_col.text_input("City", key="manual_address_city")
    manual_state = state_col.text_input("State (e.g., MA)", key="manual_address_state")
    manual_zip = st.text_input("ZIP", key="manual_address_zip")

    line1 = manual_line1.strip()
    city = manual_city.strip()
    state = manual_state.strip().upper()
    postal = manual_zip.strip()

    if line1 and city and state and postal:
        return Address(line1=line1, city=city, state=state, zip=postal)

    return None


def analysis_choice() -> str:
    options = ["Rental Analysis", "Renovation Flip Analysis"]
    current = st.session_state.get("analysis_type", options[0])
    index = options.index(current) if current in options else 0
    return st.sidebar.radio("Analysis Type", options, index=index)


def rental_form() -> Tuple[RentalAssumptions, float]:
    st.subheader("Rental Assumptions")
    _ensure_rental_defaults()

    price = st.number_input("Purchase Price", min_value=0.0, step=1000.0, key="rental_purchase_price")
    down = st.number_input("Down Payment %", min_value=0.0, max_value=100.0, step=1.0, key="rental_down_payment_pct")
    rate_pct = st.number_input("Interest Rate (annual %)", min_value=0.0, max_value=20.0, step=0.1, key="rental_interest_rate_pct")
    term_years = st.number_input("Loan Term (years)", min_value=1, max_value=40, key="rental_loan_term_years")
    vacancy_pct = st.number_input("Vacancy %", min_value=0.0, max_value=50.0, step=0.5, key="rental_vacancy_pct")
    mgmt_pct = st.number_input("Property Management %", min_value=0.0, max_value=30.0, step=0.5, key="rental_management_pct")
    maintenance = st.number_input("Maintenance Reserve (annual $)", min_value=0.0, max_value=1_000_000.0, step=100.0, key="rental_maintenance_reserve")
    capex = st.number_input("CapEx Reserve (annual $)", min_value=0.0, max_value=1_000_000.0, step=100.0, key="rental_capex_reserve")
    insurance = st.number_input("Insurance (annual $)", min_value=0.0, max_value=1_000_000.0, step=100.0, key="rental_insurance")
    hoa = st.number_input("HOA (annual $)", min_value=0.0, max_value=1_000_000.0, step=100.0, key="rental_hoa")
    hold_years = st.number_input("Hold Period (years)", min_value=1, max_value=40, key="rental_hold_years")
    target_cap = st.number_input("Target Cap Rate % (optional)", min_value=0.0, max_value=50.0, step=0.5, key="rental_target_cap")
    target_irr = st.number_input("Target IRR % (optional)", min_value=0.0, max_value=50.0, step=0.5, key="rental_target_irr")

    assumptions = RentalAssumptions(
        down_payment_pct=down,
        interest_rate_annual=rate_pct / 100,
        loan_term_years=term_years,
        vacancy_rate_pct=vacancy_pct,
        maintenance_reserve_annual=maintenance,
        capex_reserve_annual=capex,
        insurance_annual=insurance,
        hoa_annual=hoa,
        property_mgmt_pct=mgmt_pct,
        hold_period_years=hold_years,
        target_cap_rate_pct=target_cap if target_cap > 0 else None,
        target_irr_pct=target_irr if target_irr > 0 else None,
    )

    return assumptions, price



def flip_form() -> Tuple[FlipAssumptions, float]:
    st.subheader("Flip Assumptions")
    _ensure_flip_defaults()

    price = st.number_input("Candidate Purchase Price", min_value=0.0, step=1000.0, key="flip_purchase_price")
    down = st.number_input("Down Payment %", min_value=0.0, max_value=100.0, step=1.0, key="flip_down_payment_pct")
    rate_pct = st.number_input("Interest Rate (annual %)", min_value=0.0, max_value=25.0, step=0.1, key="flip_interest_rate_pct")
    term_years = st.number_input("Loan Term (years)", min_value=1, max_value=40, key="flip_loan_term_years")
    reno = st.number_input("Renovation Budget", min_value=0.0, max_value=5_000_000.0, step=1000.0, key="flip_renovation_budget")
    hold_months = st.number_input("Hold Time (months)", min_value=1, max_value=60, key="flip_hold_months")
    margin_pct = st.number_input("Target Margin (% of ARV)", min_value=0.0, max_value=100.0, step=0.5, key="flip_target_margin_pct")
    buy_pct = st.number_input("Closing Costs on Buy (% of price)", min_value=0.0, max_value=10.0, step=0.1, key="flip_closing_buy_pct")
    sell_pct = st.number_input("Closing Costs on Sell (% of ARV)", min_value=0.0, max_value=10.0, step=0.1, key="flip_closing_sell_pct")
    arv_override = st.number_input("ARV Override (optional)", min_value=0.0, max_value=100_000_000.0, step=5000.0, key="flip_arv_override")

    assumptions = FlipAssumptions(
        down_payment_pct=down,
        interest_rate_annual=rate_pct / 100,
        loan_term_years=term_years,
        renovation_budget=reno,
        hold_time_months=hold_months,
        target_margin_pct=margin_pct / 100,
        closing_pct_buy=buy_pct / 100,
        closing_pct_sell=sell_pct / 100,
        arv_override=arv_override if arv_override > 0 else None,
    )

    return assumptions, price