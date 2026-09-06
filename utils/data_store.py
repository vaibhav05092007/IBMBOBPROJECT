
"""
utils/data_store.py
Shared in-memory appointment data store backed by st.session_state.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta
import random

_STORE_KEY = "_appointments_df"

_DOCTORS   = ["Dr. Smith", "Dr. Patel", "Dr. Lee", "Dr. Garcia", "Dr. Nguyen"]
_DEPTS     = ["Cardiology", "Dermatology", "General", "Neurology", "Orthopedics"]
_STATUSES  = ["Scheduled", "Completed", "No-Show", "Cancelled"]
_GENDERS   = ["Male", "Female", "Other"]


def _generate_seed_data(n: int = 120) -> pd.DataFrame:
    """Generate realistic-looking synthetic appointment data."""
    rng = np.random.default_rng(42)
    today = date.today()

    dates = [today - timedelta(days=int(d)) for d in rng.integers(0, 90, n)]
    ages  = rng.integers(18, 85, n).tolist()

    statuses = rng.choice(
        _STATUSES,
        n,
        p=[0.25, 0.50, 0.18, 0.07],
    ).tolist()

    return pd.DataFrame(
        {
            "id":           range(1, n + 1),
            "patient_name": [f"Patient {i}" for i in range(1, n + 1)],
            "age":          ages,
            "gender":       rng.choice(_GENDERS, n).tolist(),
            "doctor":       rng.choice(_DOCTORS, n).tolist(),
            "department":   rng.choice(_DEPTS, n).tolist(),
            "date":         [pd.Timestamp(d) for d in dates],
            "status":       statuses,
            "distance_km":  np.round(rng.uniform(1, 50, n), 1).tolist(),
            "prev_noshow":  rng.integers(0, 5, n).tolist(),
        }
    )


def init_store() -> None:
    """Initialise the shared data store (idempotent)."""
    if _STORE_KEY not in st.session_state:
        st.session_state[_STORE_KEY] = _generate_seed_data()


def get_appointments_df() -> pd.DataFrame:
    """Return the full appointments DataFrame."""
    return st.session_state.get(_STORE_KEY, pd.DataFrame())


def add_appointment(record: dict) -> None:
    """Append a new appointment record (dict) to the store."""
    df = get_appointments_df()
    new_id = int(df["id"].max() + 1) if not df.empty else 1
    record["id"] = new_id
    record["status"] = record.get("status", "Scheduled")
    new_row = pd.DataFrame([record])
    st.session_state[_STORE_KEY] = pd.concat([df, new_row], ignore_index=True)


def update_status(appointment_id: int, new_status: str) -> None:
    """Update the status of an appointment by its id."""
    df = get_appointments_df()
    df.loc[df["id"] == appointment_id, "status"] = new_status
    st.session_state[_STORE_KEY] = df
