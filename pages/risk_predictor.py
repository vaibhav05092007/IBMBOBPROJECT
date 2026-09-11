"""
pages/risk_predictor.py
No-show risk predictor using a simple RandomForest trained on session data.
"""

import streamlit as st
import pandas as pd
import numpy as np
from utils.data_store import get_appointments_df

_DOCTORS  = ["Dr. Smith", "Dr. Patel", "Dr. Lee", "Dr. Garcia", "Dr. Nguyen"]
_DEPTS    = ["Cardiology", "Dermatology", "General", "Neurology", "Orthopedics"]
_GENDERS  = ["Male", "Female", "Other"]


@st.cache_resource(show_spinner="Training model…")
def _train_model(data_hash: int):
    """Train a lightweight RandomForest on the current appointment data."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import LabelEncoder

    df = get_appointments_df()
    required_columns = {
        "age", "distance_km", "prev_noshow", "gender", "department", "doctor", "status"
    }
    if len(df) < 10 or not required_columns.issubset(df.columns):
        return None, None, None

    features = df[["age", "distance_km", "prev_noshow", "gender", "department", "doctor"]].copy()
    target   = (df["status"] == "No-Show").astype(int)
    if target.nunique() < 2:
        return None, None, None

    encoders = {}
    for col in ["gender", "department", "doctor"]:
        le = LabelEncoder()
        features[col] = le.fit_transform(features[col].astype(str))
        encoders[col] = le

    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(features, target)
    return clf, encoders, features.columns.tolist()


def render():
    st.title(":material/monitoring: No-Show Risk Predictor")
    st.write(
        "Enter patient details to estimate the probability that they will miss their appointment."
    )

    df = get_appointments_df()
    # Use a simple hash of the dataframe length + no-show count as the cache key
    data_hash = hash((len(df), int((df["status"] == "No-Show").sum())))

    model, encoders, feature_cols = _train_model(data_hash)

    if model is None:
        st.warning(
            "The predictor needs at least 10 appointments with both no-show and attended records."
        )
        return

    # ── Input form ─────────────────────────────────────────────────────────────
    with st.form("predictor_form"):
        col1, col2 = st.columns(2)

        with col1:
            age         = st.number_input("Age", min_value=1, max_value=120, value=35)
            gender      = st.selectbox("Gender", _GENDERS)
            distance_km = st.slider("Distance from clinic (km)", 1, 100, 15)

        with col2:
            department  = st.selectbox("Department", _DEPTS)
            doctor      = st.selectbox("Doctor", _DOCTORS)
            prev_noshow = st.number_input("Previous no-shows", min_value=0, max_value=20, value=0)

        predict_btn = st.form_submit_button(":material/search: Predict Risk", type="primary")

    if predict_btn:
        # Encode inputs
        unknown_values = {
            field: value
            for field, value in {
                "gender": gender,
                "department": department,
                "doctor": doctor,
            }.items()
            if value not in encoders[field].classes_
        }
        if unknown_values:
            st.warning(
                "This model has not seen the selected "
                + ", ".join(unknown_values)
                + ". Add an appointment using those values and try again."
            )
            return

        input_data = {
            "age":          [int(age)],
            "distance_km":  [float(distance_km)],
            "prev_noshow":  [int(prev_noshow)],
            "gender":       [encoders["gender"].transform([gender])[0]],
            "department":   [encoders["department"].transform([department])[0]],
            "doctor":       [encoders["doctor"].transform([doctor])[0]],
        }
        X = pd.DataFrame(input_data)[feature_cols]
        prob = model.predict_proba(X)[0][1]

        # Display result
        st.divider()
        risk_pct = prob * 100

        if risk_pct < 30:
            colour, label, icon = "green", "Low Risk", ":material/check_circle:"
        elif risk_pct < 60:
            colour, label, icon = "orange", "Medium Risk", ":material/warning:"
        else:
            colour, label, icon = "red", "High Risk", ":material/dangerous:"

        st.metric(f"{icon} No-Show Probability", f"{risk_pct:.1f}%", label_delta=label)
        st.progress(int(risk_pct))

        if risk_pct >= 60:
            st.warning(
                "Consider sending a reminder call or SMS to reduce the likelihood of a no-show."
            )

    # ── Feature importance ─────────────────────────────────────────────────────
    with st.expander(":material/bar_chart: Model feature importances"):
        importance_df = (
            pd.DataFrame(
                {"feature": feature_cols, "importance": model.feature_importances_}
            )
            .sort_values("importance", ascending=False)
            .set_index("feature")
        )
        st.bar_chart(importance_df["importance"])


if __name__ == "__main__":
    render()
