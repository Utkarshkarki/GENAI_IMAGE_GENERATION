"""
backend/memory_store.py
In-process preference memory — replaces services/memory.py which depends on Streamlit.
Each session_id maps to a dict of preferences. For a single-user dev setup this is fine;
for multi-user production you'd swap this for Redis / a DB.
"""
from __future__ import annotations
from collections import defaultdict

_store: dict[str, dict] = defaultdict(dict)

SESSION = "default"  # single-user default; React can pass a session id header later


def save_preference(key: str, value, session: str = SESSION) -> None:
    _store[session][key] = value


def get_preferences(session: str = SESSION) -> dict:
    return dict(_store[session])


def clear_preference(key: str, session: str = SESSION) -> None:
    _store[session].pop(key, None)


def clear_all_preferences(session: str = SESSION) -> None:
    _store[session] = {}
