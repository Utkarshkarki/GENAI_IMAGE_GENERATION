"""
services/memory.py — Session preference memory for AdSnap Studio AI Agent.
Preferences are stored in Streamlit's session_state so they persist for the
entire browser session without touching disk.
"""

from __future__ import annotations
import streamlit as st


def _store() -> dict:
    """Return the agent_memory dict from session state, initialising if needed."""
    if "agent_memory" not in st.session_state:
        st.session_state.agent_memory = {}
    return st.session_state.agent_memory


def save_preference(key: str, value) -> None:
    """Persist a user preference (e.g. background_color: '#FFFFFF')."""
    _store()[key] = value


def get_preferences() -> dict:
    """Return all remembered preferences as a plain dict."""
    return dict(_store())


def clear_preference(key: str) -> None:
    """Remove a single preference."""
    _store().pop(key, None)


def clear_all_preferences() -> None:
    """Wipe the entire preference memory."""
    st.session_state.agent_memory = {}


def merge_with_preferences(params: dict) -> dict:
    """
    Return a new dict that fills any *missing* keys in `params` from
    stored preferences.  Explicit values in `params` are never overwritten.
    """
    merged = dict(get_preferences())
    merged.update(params)  # params wins on conflict
    return merged
