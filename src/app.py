import streamlit as st
from src.utils.logging import logger
from src.ui.ui_components import (
    address_input,
    analysis_choice,
    rental_form,
    flip_form,
    reset_rental_form_state,
    reset_flip_form_state,
)
from src.services.data_fetch import fetch_property
from src.services.analysis_service import analyze_rental, analyze_flip
from src.utils.currency import usd

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
    st.session_state.property = fetch_property(addr)
    st.session_state.result = None
    reset_rental_form_state()
    reset_flip_form_state()
    st.success("Property data loaded (mock if APIs not configured).")

prop = st.session_state.property
if prop:
    with st.expander("Pulled Data", expanded=False):
        st.json(prop.__dict__)
        st.json({
            "market_value_estimate": prop.market_value_estimate,
            "rent_estimate": prop.rent_estimate,
            "annual_taxes": prop.annual_taxes,
            "closing_cost_estimate": prop.closing_cost_estimate,
            "sources": [s.value for s in prop.sources],
        })

    if choice == "Rental Analysis":
        a, price = rental_form()
        if st.button("Run Rental Analysis"):
            res = analyze_rental(prop, a, price)
            st.session_state.result = res
    else:
        a, price = flip_form()
        if st.button("Run Flip Analysis"):
            res = analyze_flip(prop, a, price)
            st.session_state.result = res

if st.session_state.result:
    st.subheader("Results")
    r = st.session_state.result
    for k, v in r.__dict__.items():
        st.write(f"- **{k}**: {usd(v) if isinstance(v, (int, float)) else v}") 