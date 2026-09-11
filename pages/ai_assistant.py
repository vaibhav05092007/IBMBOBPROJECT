"""
pages/ai_assistant.py
Conversational AI assistant powered by Google Gemini 3.6 Flash.
The API key is entered by the user for their own session only.
"""

import streamlit as st
from utils.data_store import get_appointments_df


def _get_api_key() -> str | None:
    """Return the Gemini API key from the current session only."""
    return st.session_state.get("_gemini_api_key")


def _build_system_prompt() -> str:
    df = get_appointments_df()
    total     = len(df)
    no_shows  = int((df["status"] == "No-Show").sum())
    scheduled = int((df["status"] == "Scheduled").sum())
    return (
        "You are a helpful healthcare assistant for a clinic appointment management system. "
        "You help staff with scheduling questions, patient no-show analysis, and general "
        "healthcare admin queries.\n\n"
        f"Current clinic stats: {total} total appointments, "
        f"{scheduled} scheduled, {no_shows} no-shows recorded.\n\n"
        "Be concise, professional, and friendly. "
        "Do not reveal personal patient data."
    )


def render():
    st.title(":material/smart_toy: AI Assistant")
    st.write("Ask anything about appointments, scheduling, or patient management.")

    # ── API key handling ────────────────────────────────────────────────────────
    api_key = _get_api_key()

    if not api_key:
        with st.expander(":material/key: Enter Gemini API Key", expanded=True):
            key_input = st.text_input(
                "Gemini API Key",
                type="password",
                placeholder="AIza…",
                label_visibility="collapsed",
            )
            if st.button("Save key", type="primary"):
                if key_input.strip():
                    st.session_state["_gemini_api_key"] = key_input.strip()
                    st.success("Key saved for this session.")
                    st.rerun()
                else:
                    st.error("Please enter a valid API key.")
        st.info(
            "No Gemini API key found. "
            "Enter your own Gemini API key above to use the assistant."
        )
        return

    # ── Chat history ────────────────────────────────────────────────────────────
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Render existing messages
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ── User input ─────────────────────────────────────────────────────────────
    user_input = st.chat_input("Type your question…")

    if user_input:
        # Show user message immediately
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        # Call Gemini
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                reply = _call_gemini(api_key, user_input)
            st.markdown(reply)

        st.session_state.chat_history.append({"role": "assistant", "content": reply})

    # Clear chat button
    if st.session_state.chat_history:
        if st.button(":material/delete: Clear conversation", type="tertiary"):
            st.session_state.chat_history = []
            st.rerun()


def _call_gemini(api_key: str, user_message: str) -> str:
    """Send a message to Gemini 3.6 Flash and return the text reply."""
    try:
        import google.generativeai as genai  # type: ignore

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name="gemini-3.6-flash",
            system_instruction=_build_system_prompt(),
        )

        # Build history for multi-turn context (last 10 turns)
        history = []
        for msg in st.session_state.chat_history[:-1][-10:]:
            history.append({"role": msg["role"], "parts": [msg["content"]]})

        chat = model.start_chat(history=history)
        response = chat.send_message(user_message)
        return response.text

    except ImportError:
        return (
            "⚠️ The `google-generativeai` package is not installed. "
            "Run `pip install google-generativeai` and restart the app."
        )
    except Exception as exc:  # noqa: BLE001
        return f"⚠️ Gemini error: {exc}"
