"""
Alternative address input component using the instant autocomplete.
This provides a different UX approach for comparison.
"""

from __future__ import annotations

from typing import Optional

import streamlit as st

from ..core.models import Address
from ..services.nominatim_places import get_address_from_suggestion, get_place_suggestions
from .autocomplete_component import instant_address_autocomplete, format_suggestion_label


def alternative_address_input() -> Optional[Address]:
    """
    Alternative address input using instant autocomplete with selectbox.
    This provides a different UX - suggestions appear immediately in a dropdown.
    """
    
    st.subheader("Property Address (Alternative)")
    
    # Use the instant autocomplete component
    selected_suggestion = instant_address_autocomplete(
        suggestions_func=get_place_suggestions,
        placeholder="Start typing an address...",
        max_suggestions=5,
        key="alternative_property_address_autocomplete"
    )
    
    # If user selected a suggestion, populate the manual fields
    if selected_suggestion:
        address = get_address_from_suggestion(selected_suggestion)
        if address:
            st.session_state.manual_address_line1 = address.line1
            st.session_state.manual_address_city = address.city
            st.session_state.manual_address_state = address.state
            st.session_state.manual_address_zip = address.zip
            st.success(f"✅ Address selected: {format_suggestion_label(selected_suggestion)}")
    
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
