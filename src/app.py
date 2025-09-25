from __future__ import annotations

import streamlit as st

from src.services.analysis_service import analyze_flip, analyze_rental
from src.services.data_fetch import fetch_property
from src.ui.ui_components import (
    address_input,
    analysis_choice,
    flip_form,
    rental_form,
    reset_flip_form_state,
    reset_rental_form_state,
)
from src.utils.currency import usd
from src.utils.logging import logger


st.set_page_config(page_title="Property Underwriter", layout="wide")

if "address" not in st.session_state:
    st.session_state.address = None
if "property" not in st.session_state:
    st.session_state.property = None
if "result" not in st.session_state:
    st.session_state.result = None
if "analysis_type" not in st.session_state:
    st.session_state.analysis_type = "Rental Analysis"

st.title("🏠 Property Underwriter (MVP)")

addr = address_input()
choice = analysis_choice()
st.session_state.analysis_type = choice

if addr and st.button("Fetch Property Data"):
    st.session_state.address = addr
    logger.info("Fetching property data for %s", addr)
    st.session_state.property = fetch_property(addr)
    st.session_state.result = None
    reset_rental_form_state()
    reset_flip_form_state()
    st.success("Property data loaded (mock if APIs not configured).")

prop = st.session_state.property
if prop:
    with st.expander("Pulled Data", expanded=False):
        st.json(prop.__dict__)
        st.json(
            {
                "market_value_estimate": prop.market_value_estimate,
                "rent_estimate": prop.rent_estimate,
                "annual_taxes": prop.annual_taxes,
                "closing_cost_estimate": prop.closing_cost_estimate,
                "sources": [s.value for s in prop.sources],
            }
        )

    if choice == "Rental Analysis":
        assumptions, price = rental_form()
        if st.button("Run Rental Analysis"):
            logger.info("Running rental analysis for %s", prop.address)
            result = analyze_rental(prop, assumptions, price)
            st.session_state.result = result
    else:
        assumptions, price = flip_form()
        if st.button("Run Flip Analysis"):
            logger.info("Running flip analysis for %s", prop.address)
            result = analyze_flip(prop, assumptions, price)
            st.session_state.result = result

if st.session_state.result:
    st.subheader("Results")
    result = st.session_state.result
    for key, value in result.__dict__.items():
        if isinstance(value, (int, float)):
            st.write(f"- **{key}**: {usd(value)}")
        else:
            st.write(f"- **{key}**: {value}")
