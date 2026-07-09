import os
from typing import Any


def get_secret(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value:
        return value

    try:
        import streamlit as st

        secret_value: Any = st.secrets.get(name, default)
        if isinstance(secret_value, str) and secret_value:
            return secret_value
        if secret_value is None:
            return default
        return str(secret_value)
    except Exception:
        return default
