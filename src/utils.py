import os
import time

import pandas as pd
import plotly.express as px
import streamlit as st
from scipy.stats import zscore


def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        password = os.getenv("STREAMLIT_PASSWORD")
        if not password:
            st.error("😕 Password not set")
            return False
        if st.session_state["password"] == password:
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


def load_smart_meter_data():
    """Loads the smart meter data from the CSV file."""
    df = pd.read_csv("src/smart_meter_data.csv", index_col=0, parse_dates=True)
    return df


def detect_anomalies(df):
    """
    Detects anomalies in energy usage from smart meter data.

    Simple anomaly detection using z-score exceeding 2 for daily usage.
    """

    # Aggregate the data to daily usage
    df_daily = df.resample("D").sum()

    # Calculate the Z-score for daily usage
    df_daily["zscore"] = zscore(df_daily["usage"])

    # Identify outliers (e.g., Z-score > 2 or < -2)
    df_daily["outlier"] = df_daily["zscore"].abs() > 2

    # if there are any outliers, return the dates
    if df_daily["outlier"].any():
        outliers = df_daily[df_daily["outlier"]].index
        return outliers
    else:
        return None


def plot_anomalies(df, outliers):
    """Plots the anomalies in the energy usage."""
    # plot original data with outliers highlighted with a red box covering the day
    fig = px.line(df, x=df.index, y="usage", title="Daily Usage with Outliers Highlighted")
    for outlier in outliers:
        fig.add_vrect(
            x0=outlier,
            x1=outlier + pd.Timedelta(days=1),
            fillcolor="red",
            opacity=0.25,
            line_width=0,
            annotation_text="Outlier",
        )
    
    return fig
