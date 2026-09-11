"""
pages/booking.py
Book a new appointment.
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from utils.data_store import add_appointment, get_appointments_df

_DOCTORS  = ["Dr. Smith", "Dr. Patel", "Dr. Lee", "Dr. Garcia", "Dr. Nguyen"]
_DEPTS    = ["Cardiology", "Dermatology", "General", "Neurology", "Orthopedics"]
_GENDERS  = ["Male", "Female", "Other"]


def render():
    st.title(":material/calendar_add_on: Book an Appointment")
    st.write("Fill in the details below to schedule a new appointment.")

    with st.form("booking_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            patient_name = st.text_input("Patient name")
            age          = st.number_input("Age", min_value=1, max_value=120, value=30)
            gender       = st.selectbox("Gender", _GENDERS)

        with col2:
            doctor     = st.selectbox("Doctor", _DOCTORS)
            department = st.selectbox("Department", _DEPTS)
            appt_date  = st.date_input(
                "Appointment date",
                value=date.today() + timedelta(days=1),
                min_value=date.today(),
            )

        distance_km = st.slider("Distance from clinic (km)", 1, 100, 10)
        prev_noshow = st.number_input(
            "Previous no-shows (patient history)", min_value=0, max_value=20, value=0
        )

        submitted = st.form_submit_button(":material/check: Confirm Booking", type="primary")

    if submitted:
        if not patient_name.strip():
            st.error("Please enter the patient name.")
        else:
            add_appointment(
                {
                    "patient_name": patient_name.strip(),
                    "age":          int(age),
                    "gender":       gender,
                    "doctor":       doctor,
                    "department":   department,
                    "date":         pd.Timestamp(appt_date),
                    "distance_km":  float(distance_km),
                    "prev_noshow":  int(prev_noshow),
                }
            )
            st.success(
                f"✅ Appointment booked for **{patient_name}** with **{doctor}** "
                f"on **{appt_date.strftime('%d %b %Y')}**."
            )

    # Recent bookings table
    st.divider()
    st.subheader("Recent appointments")
    df = get_appointments_df()
    if not df.empty:
        st.dataframe(
            df.sort_values("date", ascending=False).head(20)[
                ["id", "patient_name", "age", "doctor", "department", "date", "status"]
            ],
            hide_index=True,
        )
    else:
        st.info("No appointments yet.")


if __name__ == "__main__":
    render()
