import hmac
import os
import time

import streamlit as st


def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        password = os.getenv("STREAMLIT_PASSWORD")
        if hmac.compare_digest(st.session_state["password"], password):
            st.session_state["password_correct"] = True
            st.session_state["show_success"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        if st.session_state.get("show_success", False):
            placeholder = st.empty()
            placeholder.success("🎉 Password correct")
            time.sleep(1.5)
            placeholder.empty()
            st.session_state["show_success"] = False
        return True

    # Show input for password.
    st.text_input("Password", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False
