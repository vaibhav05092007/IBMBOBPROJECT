"""
HealthCare AI — Main Application Entry Point
Run with: streamlit run app.py
"""

import streamlit as st
import sys, os

# ── Path setup ─────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

# ── Page config — MUST be first Streamlit call ────────────────────────────────
st.set_page_config(
    page_title="HealthCare AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Shared data store init ─────────────────────────────────────────────────────
from utils.data_store import init_store
init_store()

# ── Page imports ───────────────────────────────────────────────────────────────
from pages.booking        import render as render_booking
from pages.admin_dashboard import render as render_admin
from pages.risk_predictor  import render as render_risk
from pages.ai_assistant    import render as render_ai


# ── Sidebar navigation and live statistics ────────────────────────────────────
def _sidebar():
    with st.sidebar:
        st.markdown(
            "## 🏥 HealthCare AI\n"
            "*AI-Powered Appointment Management*"
        )
        st.divider()

        nav = st.radio(
            "Navigation",
            options=[
                "📅 Book Appointment",
                "📊 Admin Dashboard",
                "🤖 No-Show Predictor",
                "💬 AI Assistant",
            ],
            key="nav_radio",
            label_visibility="collapsed",
        )

        st.divider()

        # Live stats in sidebar
        from utils.data_store import get_appointments_df
        df = get_appointments_df()
        import pandas as pd
        from datetime import date
        today = pd.Timestamp(date.today())
        today_count   = len(df[df["date"] == today])
        noshow_total  = (df["status"] == "No-Show").sum()
        total         = len(df)

        st.markdown("### 📊 Quick Stats")
        st.markdown(f"- **Appointments:** {total}")
        st.markdown(f"- **Today:** {today_count}")
        st.markdown(f"- **No-Shows:** {noshow_total} ({noshow_total/total*100:.1f}%)" if total else "- **No-Shows:** 0")

        st.divider()
        st.caption("Built with Streamlit · Gemini 3.6 Flash · scikit-learn")

    return nav


# ── Router ─────────────────────────────────────────────────────────────────────
def main():
    nav = _sidebar()

    if nav == "📅 Book Appointment":
        render_booking()
    elif nav == "📊 Admin Dashboard":
        render_admin()
    elif nav == "🤖 No-Show Predictor":
        render_risk()
    elif nav == "💬 AI Assistant":
        render_ai()


if __name__ == "__main__":
    main()
