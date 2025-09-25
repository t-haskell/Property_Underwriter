"""Enhanced address autocomplete component for Streamlit.

Provides real-time suggestions as the user types using a more Streamlit-native approach.
"""

from typing import Callable, Dict, List, Optional
import time

import streamlit as st


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
            suggestions = suggestions_func(trimmed_query)
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
        
        # Create columns for suggestions
        cols = st.columns(min(len(suggestions), 3))
        
        for i, suggestion in enumerate(suggestions):
            col_idx = i % 3
            
            with cols[col_idx]:
                # Create a button for each suggestion
                suggestion_text = suggestion.get("description", suggestion.get("text", ""))
                if st.button(
                    suggestion_text[:50] + "..." if len(suggestion_text) > 50 else suggestion_text,
                    key=f"{key}_suggestion_{i}",
                    help="Click to select this address"
                ):
                    # User selected this suggestion
                    st.session_state[f"{key}_selected"] = suggestion
                    st.session_state[f"{key}_query"] = suggestion_text
                    st.session_state[f"{key}_input"] = suggestion_text
                    st.session_state[f"{key}_suggestions"] = []
                    st.session_state[f"{key}_last_query"] = suggestion_text
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
            suggestions = suggestions_func(query.strip())
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
        suggestion_options = [""] + [s.get("description", s.get("text", "")) for s in suggestions]
        
        selected_text = st.selectbox(
            "Select an address:",
            options=suggestion_options,
            key=f"{key}_selectbox",
            help="Choose from the suggestions above"
        )
        
        if selected_text:
            # Find the selected suggestion
            selected_suggestion = next(
                (s for s in suggestions if s.get("description", s.get("text", "")) == selected_text),
                None
            )
            if selected_suggestion:
                st.session_state[f"{key}_selected"] = selected_suggestion
                st.session_state[f"{key}_query"] = selected_text
                st.rerun()
    
    # Return selected suggestion
    if st.session_state[f"{key}_selected"]:
        selected = st.session_state[f"{key}_selected"]
        st.session_state[f"{key}_selected"] = None  # Reset after use
        return selected
    
    return None
