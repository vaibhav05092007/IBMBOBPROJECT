"""
pages/admin_dashboard.py
Overview metrics and appointment management for admins.
"""

import streamlit as st
import pandas as pd
from utils.data_store import get_appointments_df, update_status

_STATUSES = ["Scheduled", "Completed", "No-Show", "Cancelled"]


def render():
    st.title(":material/dashboard: Admin Dashboard")

    df = get_appointments_df()

    if df.empty:
        st.info("No appointment data available.")
        return

    # ── KPI row ────────────────────────────────────────────────────────────────
    total       = len(df)
    scheduled   = (df["status"] == "Scheduled").sum()
    completed   = (df["status"] == "Completed").sum()
    no_shows    = (df["status"] == "No-Show").sum()
    ns_rate     = no_shows / total * 100 if total else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Appointments", total)
    k2.metric("Scheduled",          int(scheduled))
    k3.metric("Completed",          int(completed))
    k4.metric("No-Show Rate",       f"{ns_rate:.1f}%")

    st.divider()

    # ── Charts ─────────────────────────────────────────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Appointments by department")
        dept_counts = df.groupby("department").size().reset_index(name="count")
        st.bar_chart(dept_counts.set_index("department")["count"])

    with col_b:
        st.subheader("Status breakdown")
        status_counts = df["status"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]
        st.bar_chart(status_counts.set_index("status")["count"])

    st.divider()

    # ── Daily trend ────────────────────────────────────────────────────────────
    st.subheader("Daily appointment trend (last 30 days)")
    today = pd.Timestamp("today").normalize()
    cutoff = today - pd.Timedelta(days=30)
    trend = (
        df[df["date"] >= cutoff]
        .groupby("date")
        .size()
        .reset_index(name="appointments")
        .set_index("date")
    )
    if not trend.empty:
        st.line_chart(trend["appointments"])
    else:
        st.info("No data in the last 30 days.")

    st.divider()

    # ── Manage individual appointments ─────────────────────────────────────────
    st.subheader("Manage appointments")

    with st.expander("Filter & update status"):
        filter_status = st.multiselect(
            "Filter by status", _STATUSES, default=_STATUSES
        )
        filtered = df[df["status"].isin(filter_status)].sort_values("date", ascending=False)

        st.dataframe(
            filtered[["id", "patient_name", "age", "doctor", "department", "date", "status"]],
            hide_index=True,
        )

        st.write("**Update a status**")
        appt_id    = st.number_input("Appointment ID", min_value=1, step=1)
        new_status = st.selectbox("New status", _STATUSES, key="admin_new_status")
        if st.button(":material/edit: Update", type="primary"):
            if appt_id in df["id"].values:
                update_status(int(appt_id), new_status)
                st.success(f"Appointment {appt_id} updated to **{new_status}**.")
                st.rerun()
            else:
                st.error(f"Appointment ID {appt_id} not found.")


if __name__ == "__main__":
    render()
