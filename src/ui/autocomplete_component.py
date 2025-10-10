"""Enhanced address autocomplete component for Streamlit.

Provides real-time suggestions as the user types using a more Streamlit-native approach.
"""

from typing import Callable, Dict, List, Optional
import time

import streamlit as st


def format_suggestion_label(suggestion: Dict[str, str]) -> str:
    """Return a concise, user-friendly label for an address suggestion."""
    street = (suggestion.get("street") or suggestion.get("street_address") or "").strip()
    city = (suggestion.get("city") or "").strip()
    state = (suggestion.get("state") or "").strip()
    postal = (suggestion.get("zip") or suggestion.get("postal_code") or "").strip()
    fallback = (suggestion.get("description") or suggestion.get("text") or "").strip()

    # Assemble `Street, City, ST ZIP` when possible.
    locality = " ".join(part for part in [state, postal] if part).strip()
    address_parts = [part for part in [street, city, locality] if part]
    if address_parts:
        return ", ".join(address_parts)

    if fallback:
        return fallback

    fallback_identifier = suggestion.get("place_id", "").strip()
    if fallback_identifier:
        return f"Suggestion {fallback_identifier}"
    return "Address suggestion"


def enhanced_address_autocomplete(
    suggestions_func: Callable[[str], List[Dict[str, str]]],
    placeholder: str = "Start typing an address...",
    max_suggestions: int = 5,
    key: str = "enhanced_address_autocomplete",
    min_chars: int = 2,
    debounce_seconds: float = 0.15,
) -> Optional[Dict[str, str]]:
    """
    Enhanced address autocomplete with immediate suggestions.
    Uses Streamlit's native components with improved UX.
    
    Args:
        suggestions_func: Function that takes a query string and returns list of suggestions
        placeholder: Placeholder text for the input field
        max_suggestions: Maximum number of suggestions to show
        key: Unique key for the component
    
    Returns:
        Selected suggestion dict or None
    """
    
    # Initialize session state
    if f"{key}_query" not in st.session_state:
        st.session_state[f"{key}_query"] = ""
    if f"{key}_suggestions" not in st.session_state:
        st.session_state[f"{key}_suggestions"] = []
    if f"{key}_selected" not in st.session_state:
        st.session_state[f"{key}_selected"] = None
    if f"{key}_last_query" not in st.session_state:
        st.session_state[f"{key}_last_query"] = ""
    if f"{key}_last_fetch_ts" not in st.session_state:
        st.session_state[f"{key}_last_fetch_ts"] = 0.0

    # Main input field (reruns on every keystroke)
    query = st.text_input(
        "",
        value=st.session_state[f"{key}_query"],
        key=f"{key}_input",
        placeholder=placeholder,
        label_visibility="collapsed",
        help=f"Type at least {min_chars} characters to see suggestions",
    )

    # Persist the latest query so downstream components can use it
    if query != st.session_state[f"{key}_query"]:
        st.session_state[f"{key}_query"] = query

    trimmed_query = query.strip()
    now = time.time()

    # Get suggestions when the user has typed enough characters.
    should_fetch = (
        len(trimmed_query) >= min_chars
        and (
            trimmed_query != st.session_state[f"{key}_last_query"]
            or (now - st.session_state[f"{key}_last_fetch_ts"]) >= debounce_seconds
        )
    )

    if should_fetch:
        try:
            suggestions = suggestions_func(trimmed_query, limit=max_suggestions)
            st.session_state[f"{key}_suggestions"] = suggestions[:max_suggestions]
            st.session_state[f"{key}_last_query"] = trimmed_query
            st.session_state[f"{key}_last_fetch_ts"] = now
        except Exception as e:
            st.error(f"Error fetching suggestions: {e}")
            st.session_state[f"{key}_suggestions"] = []
            st.session_state[f"{key}_last_fetch_ts"] = now

    # Clear suggestions if query is too short
    elif len(trimmed_query) < min_chars:
        st.session_state[f"{key}_suggestions"] = []
        st.session_state[f"{key}_last_query"] = trimmed_query

    # Display suggestions
    suggestions = st.session_state[f"{key}_suggestions"]
    if suggestions:
        st.write("**Suggestions:**")

        for i, suggestion in enumerate(suggestions):
            base_label = format_suggestion_label(suggestion)
            readable = base_label or suggestion.get("description", "") or f"Suggestion {i + 1}"
            help_text = suggestion.get("description") or "Click to select this address"

            label_col, button_col = st.columns([0.82, 0.18])
            with label_col:
                st.markdown(f"{i + 1}. {readable}")
            with button_col:
                if st.button(
                    "Select",
                    key=f"{key}_suggestion_{i}",
                    help=help_text,
                    use_container_width=True,
                    type="primary",
                ):
                    st.session_state[f"{key}_selected"] = suggestion
                    display_value = readable
                    st.session_state[f"{key}_query"] = display_value
                    st.session_state[f"{key}_input"] = display_value
                    st.session_state[f"{key}_suggestions"] = []
                    st.session_state[f"{key}_last_query"] = display_value
                    st.session_state[f"{key}_last_fetch_ts"] = time.time()
                    st.rerun()
    
    # Return selected suggestion
    if st.session_state[f"{key}_selected"]:
        selected = st.session_state[f"{key}_selected"]
        st.session_state[f"{key}_selected"] = None  # Reset after use
        return selected
    
    return None


def instant_address_autocomplete(
    suggestions_func: Callable[[str], List[Dict[str, str]]],
    placeholder: str = "Start typing an address...",
    max_suggestions: int = 5,
    key: str = "instant_address_autocomplete"
) -> Optional[Dict[str, str]]:
    """
    Instant address autocomplete with dropdown-style suggestions.
    Uses Streamlit's selectbox with dynamic options for better UX.
    
    Args:
        suggestions_func: Function that takes a query string and returns list of suggestions
        placeholder: Placeholder text for the input field
        max_suggestions: Maximum number of suggestions to show
        key: Unique key for the component
    
    Returns:
        Selected suggestion dict or None
    """
    
    # Initialize session state
    if f"{key}_query" not in st.session_state:
        st.session_state[f"{key}_query"] = ""
    if f"{key}_suggestions" not in st.session_state:
        st.session_state[f"{key}_suggestions"] = []
    if f"{key}_selected" not in st.session_state:
        st.session_state[f"{key}_selected"] = None
    if f"{key}_last_query" not in st.session_state:
        st.session_state[f"{key}_last_query"] = ""
    
    # Input field
    query = st.text_input(
        placeholder,
        value=st.session_state[f"{key}_query"],
        key=f"{key}_input"
    )
    
    # Update session state
    st.session_state[f"{key}_query"] = query
    
    # Get suggestions if query changed and is long enough
    if query != st.session_state[f"{key}_last_query"] and len(query.strip()) >= 2:
        try:
            suggestions = suggestions_func(query.strip(), limit=max_suggestions)
            st.session_state[f"{key}_suggestions"] = suggestions[:max_suggestions]
            st.session_state[f"{key}_last_query"] = query
        except Exception as e:
            st.error(f"Error fetching suggestions: {e}")
            st.session_state[f"{key}_suggestions"] = []
    
    # Clear suggestions if query is too short
    elif len(query.strip()) < 2:
        st.session_state[f"{key}_suggestions"] = []
        st.session_state[f"{key}_last_query"] = query
    
    # Display suggestions as selectbox
    suggestions = st.session_state[f"{key}_suggestions"]
    if suggestions:
        option_labels = ["Select an address"] + [
            f"#{index + 1} {format_suggestion_label(s) or s.get('description', '').strip() or 'Suggestion'}"
            for index, s in enumerate(suggestions)
        ]

        selected_option = st.selectbox(
            "Select an address:",
            options=option_labels,
            key=f"{key}_selectbox",
            help="Choose from the suggestions above"
        )

        if selected_option and selected_option != option_labels[0]:
            selected_index = option_labels.index(selected_option) - 1
            if 0 <= selected_index < len(suggestions):
                selected_suggestion = suggestions[selected_index]
                st.session_state[f"{key}_selected"] = selected_suggestion
                display_value = format_suggestion_label(selected_suggestion) or selected_suggestion.get("description", "")
                st.session_state[f"{key}_query"] = display_value
                st.session_state[f"{key}_suggestions"] = []
                st.session_state[f"{key}_last_query"] = selected_option
                st.rerun()
    
    # Return selected suggestion
    if st.session_state[f"{key}_selected"]:
        selected = st.session_state[f"{key}_selected"]
        st.session_state[f"{key}_selected"] = None  # Reset after use
        return selected
    
    return None
