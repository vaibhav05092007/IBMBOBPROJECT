
"""
utils/data_store.py
Shared appointment data store backed by session state and a local JSON file.
"""

import json
import os
from datetime import date, timedelta

import numpy as np
import pandas as pd
import streamlit as st

_STORE_KEY = "_appointments_df"
_DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "appointments_data.json")

_DOCTORS = ["Dr. Smith", "Dr. Patel", "Dr. Lee", "Dr. Garcia", "Dr. Nguyen"]
_DEPTS = ["Cardiology", "Dermatology", "General", "Neurology", "Orthopedics"]
_STATUSES = ["Scheduled", "Completed", "No-Show", "Cancelled"]
_GENDERS = ["Male", "Female", "Other"]


def _ensure_store_file() -> None:
    os.makedirs(os.path.dirname(_DATA_FILE), exist_ok=True)
    if not os.path.exists(_DATA_FILE):
        with open(_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


def _load_disk_store() -> pd.DataFrame:
    _ensure_store_file()
    try:
        with open(_DATA_FILE, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except (json.JSONDecodeError, OSError):
        return pd.DataFrame()

    if not payload:
        return pd.DataFrame()

    df = pd.DataFrame(payload)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    return df


def _save_disk_store(df: pd.DataFrame) -> None:
    _ensure_store_file()
    if df.empty:
        payload = []
    else:
        save_df = df.copy()
        if "date" in save_df.columns:
            save_df["date"] = pd.to_datetime(save_df["date"]).dt.strftime("%Y-%m-%d")
        payload = save_df.to_dict(orient="records")

    with open(_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def _generate_seed_data(n: int = 120) -> pd.DataFrame:
    """Generate realistic-looking synthetic appointment data."""
    rng = np.random.default_rng(42)
    today = date.today()

    dates = [today - timedelta(days=int(d)) for d in rng.integers(0, 90, n)]
    ages = rng.integers(18, 85, n).tolist()

    statuses = rng.choice(
        _STATUSES,
        n,
        p=[0.25, 0.50, 0.18, 0.07],
    ).tolist()

    return pd.DataFrame(
        {
            "id": range(1, n + 1),
            "patient_name": [f"Patient {i}" for i in range(1, n + 1)],
            "age": ages,
            "gender": rng.choice(_GENDERS, n).tolist(),
            "doctor": rng.choice(_DOCTORS, n).tolist(),
            "department": rng.choice(_DEPTS, n).tolist(),
            "date": [pd.Timestamp(d) for d in dates],
            "status": statuses,
            "distance_km": np.round(rng.uniform(1, 50, n), 1).tolist(),
            "prev_noshow": rng.integers(0, 5, n).tolist(),
        }
    )


def init_store() -> None:
    """Initialise the shared data store (idempotent), keeping it persistent on disk."""
    _ensure_store_file()
    if _STORE_KEY not in st.session_state:
        disk_df = _load_disk_store()
        if disk_df.empty:
            st.session_state[_STORE_KEY] = _generate_seed_data()
            _save_disk_store(st.session_state[_STORE_KEY])
        else:
            st.session_state[_STORE_KEY] = disk_df


def get_appointments_df() -> pd.DataFrame:
    """Return the full appointments DataFrame."""
    if _STORE_KEY not in st.session_state:
        init_store()
    return st.session_state[_STORE_KEY].copy()


def add_appointment(record: dict) -> None:
    """Append a new appointment record (dict) to the store."""
    df = get_appointments_df()
    new_id = int(df["id"].max() + 1) if not df.empty else 1
    record = dict(record)
    record["id"] = new_id
    record["status"] = record.get("status", "Scheduled")
    new_row = pd.DataFrame([record])
    st.session_state[_STORE_KEY] = pd.concat([df, new_row], ignore_index=True)
    _save_disk_store(st.session_state[_STORE_KEY])


def update_status(appointment_id: int, new_status: str) -> None:
    """Update the status of an appointment by its id."""
    df = get_appointments_df()
    df.loc[df["id"] == appointment_id, "status"] = new_status
    st.session_state[_STORE_KEY] = df
    _save_disk_store(df)
