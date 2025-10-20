from __future__ import annotations

from typing import Optional, Union

import streamlit as st

from src.core.models import FlipResult, RentalResult
from src.services.analysis_service import analyze_flip, analyze_rental
from src.services.data_fetch import fetch_property
from src.services.persistence import get_repository
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


repository = get_repository()


ResultType = Union[RentalResult, FlipResult]


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

result_state: Optional[ResultType] = st.session_state.result

if addr and st.button("Fetch Property Data"):
    st.session_state.address = addr
    logger.info("Fetching property data for %s", addr)
    st.session_state.property = fetch_property(addr)
    st.session_state.result = None
    result_state = None
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
        rental_assumptions, rental_price = rental_form()
        if st.button("Run Rental Analysis"):
            logger.info("Running rental analysis for %s", prop.address)
            rental_result = analyze_rental(prop, rental_assumptions, rental_price)
            repository.record_analysis(
                prop,
                analysis_type="rental",
                purchase_price=rental_price,
                assumptions=rental_assumptions.model_dump(),
                result=rental_result,
            )
            result_state = rental_result
            st.session_state.result = rental_result
    else:
        flip_assumptions, flip_price = flip_form()
        if st.button("Run Flip Analysis"):
            logger.info("Running flip analysis for %s", prop.address)
            flip_result = analyze_flip(prop, flip_assumptions, flip_price)
            repository.record_analysis(
                prop,
                analysis_type="flip",
                purchase_price=flip_price,
                assumptions=flip_assumptions.model_dump(),
                result=flip_result,
            )
            result_state = flip_result
            st.session_state.result = flip_result

    if result_state:
        st.subheader("Results")
        for key, value in result_state.__dict__.items():
            if isinstance(value, (int, float)):
                st.write(f"- **{key}**: {usd(value)}")
            else:
                st.write(f"- **{key}**: {value}")
