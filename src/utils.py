import os
import time

import numpy as np
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


def load_weather_data():
    """Loads the weather data from the CSV file."""
    df = pd.read_csv("src/weather_data.csv", index_col=0, parse_dates=True)
    return df


def detect_daily_anomalies(df):
    """
    Detects anomalies in energy usage from smart meter data.

    Simple anomaly detection using z-score exceeding 2 for daily usage.
    """

    # Aggregate the data to daily usage
    df_daily = df.resample("D").sum()

    # Calculate the Z-score for daily usage
    df_daily["zscore"] = zscore(df_daily["usage"])

    # Identify anomalies
    df_daily["anomalies"] = df_daily["zscore"] > 2

    # if there are any anomalies, return the dates
    if df_daily["anomalies"].any():
        anomalies = df_daily[df_daily["anomalies"]].index
        return anomalies
    else:
        return None


def detect_prolonged_anomalies(df, min_consecutive_days=3, zscore_threshold=1.5):
    """
    Detects prolonged anomalies in energy usage from smart meter data.

    Anomaly detection using the average z-score exceeding a threshold for a prolonged period.

    Parameters:
    df (pd.DataFrame): DataFrame containing the energy usage data with a datetime index.
    min_consecutive_days (int): Minimum number of consecutive days to consider as a prolonged anomaly.
    zscore_threshold (float): Z-score threshold for detecting anomalies.

    Returns:
    pd.DataFrame: DataFrame with the anomaly_window column indicating prolonged anomalies.
    """

    # Aggregate the data to daily usage
    df_daily = df.resample("D").sum()

    # Calculate the Z-score for daily usage
    df_daily["zscore"] = zscore(df_daily["usage"])

    # Initialize a column to mark prolonged anomalies
    df_daily["prolonged_anomaly_length"] = 0

    # Sliding window to calculate the average Z-score over periods
    for window_size in range(min_consecutive_days, len(df_daily) + 1):
        avg_zscore = df_daily["zscore"].rolling(window=window_size).mean()
        prolonged_anomaly = (avg_zscore > zscore_threshold).astype(int) * window_size
        df_daily["prolonged_anomaly_length"] = np.maximum(
            df_daily["prolonged_anomaly_length"], prolonged_anomaly
        )

    # Create prolonged_anomaly_window column
    df_daily["anomaly_window"] = False
    for i in range(len(df_daily)):
        if df_daily["prolonged_anomaly_length"].iloc[i] > 0:
            start_idx = i - df_daily["prolonged_anomaly_length"].iloc[i] + 1
            df_daily.iloc[start_idx : i + 1, df_daily.columns.get_loc("anomaly_window")] = True

    # if there are any outliers, return the dates
    if df_daily["anomaly_window"].any():
        anomalies = df_daily[df_daily["anomaly_window"]].index
        # get start and end dates of each of the prolonged anomaly windows
        prolonged_anomalies = []
        for i in range(len(anomalies)):
            if i == 0:
                start_date = anomalies[i]
            elif anomalies[i] != anomalies[i - 1] + pd.Timedelta(days=1):
                prolonged_anomalies.append((start_date, anomalies[i - 1]))
                start_date = anomalies[i]
            elif i == len(anomalies) - 1:
                prolonged_anomalies.append((start_date, anomalies[i]))
        return prolonged_anomalies
    else:
        return None


def plot_anomalies(df, anomalies, prolonged_anomalies):
    """Plots the anomalies in the energy usage."""
    # plot original data with outliers highlighted with a red box covering the day
    fig = px.line(
        df, x=df.index, y="usage", title="Daily Usage with Daily and Prolonged Anomalies Highlighted"
    )
    if anomalies is not None:
        for anomaly in anomalies:
            fig.add_vrect(
                x0=anomaly,
                x1=anomaly + pd.Timedelta(days=1),
                fillcolor="yellow",
                opacity=0.25,
                line_width=0,
                annotation_text="daily anomaly",
            )

    if prolonged_anomalies is not None:
        for anomaly in prolonged_anomalies:
            fig.add_vrect(
                x0=anomaly[0],
                x1=anomaly[1] + pd.Timedelta(days=1),
                fillcolor="red",
                opacity=0.25,
                line_width=0,
                annotation_text="prolonged anomaly",
            )

    return fig


def generate_anomaly_text(
    anomalies,
    prolonged_anomalies,
    average_temperature_str,
    anomaly_temperatures_str,
    prolonged_anomaly_temperatures_str,
):
    anomaly_text = ""
    if anomalies is not None:
        anomalies_str = ", ".join(anomalies.strftime("%Y-%m-%d"))
        anomaly_text = (
            anomaly_text
            + f"""Anomalies have been detected in the customer's energy usage. \
        The anomalies are on the following dates: {anomalies_str}. {anomaly_temperatures_str}. \
        """
        )
    if prolonged_anomalies is not None:
        prolonged_anomalies_str = ", ".join(
            [
                "prolonged anomaly "
                + str(i + 1)
                + ": "
                + prolonged_anomalies[i][0].strftime("%Y-%m-%d")
                + " to "
                + prolonged_anomalies[i][1].strftime("%Y-%m-%d")
                for i in range(len(prolonged_anomalies))
            ]
        )
        anomaly_text = (
            anomaly_text
            + f"""Prolonged anomalies have been detected in the customer's energy usage. \
        The prolonged anomalies occured on the following dates:  {prolonged_anomalies_str}. \
        These are more serious as they have lasted for more than 3 days, so may have a clearer \
        underlying cause that needs to be addressed. Prolonged anomalies can be caused by \
        things such as a device being left on, or a device consuming more power than it was previously. \
        {prolonged_anomaly_temperatures_str}. """
        )
    if anomalies is not None or prolonged_anomalies is not None:
        anomaly_text = (
            anomaly_text
            + "Help the user to identify the causes of each of the anomalies and suggest ways to fix them."
            + " You should also compare the temperature during the anomalies against the average temperature for the location."
        )
    else:
        anomaly_text = """No anomalies have been detected in the customer's energy usage. \
        You may still help the user to address any concerns they have about their energy usage."""
    anomaly_text = anomaly_text + f" {average_temperature_str}."

    return anomaly_text


def analyse_weather_data(df, anomalies, prolonged_anomalies):
    """
    Analyse weather data to identify correlations with energy usage anomalies.

    Parameters:
    df (pd.DataFrame): DataFrame containing weather data with a datetime index.
    anomalies (list): List of dates with energy usage anomalies.
    prolonged_anomalies (list): List of tuples with start and end dates of prolonged anomalies.

    Returns:
    pd.DataFrame: DataFrame with weather data during anomalies.
    """

    # resample to daily data
    df_daily = df.resample("D").mean()

    # calculate average temperature
    average_temperature = df_daily["temperature"].mean()
    average_temperature_str = "Average temperature for location (°C): {:.2f}".format(average_temperature)

    # calculate average temperature for each anomaly
    anomaly_temperatures_str = None
    if anomalies is not None:
        anomaly_temperatures = {}
        for anomaly in anomalies:
            anomaly_temperatures[anomaly] = df_daily.loc[anomaly, "temperature"]

        anomaly_temperatures_str = "Temperature during anomalies (°C): " + ", ".join(
            [
                f"[{date.strftime('%Y-%m-%d')}: {temperature:.2f}]"
                for date, temperature in anomaly_temperatures.items()
            ]
        )

    # calculate average temperature for each prolonged anomaly
    prolonged_anomaly_temperatures_str = None
    if prolonged_anomalies is not None:
        prolonged_anomaly_temperatures = {}
        for start_date, end_date in prolonged_anomalies:
            prolonged_anomaly_temperatures[(start_date, end_date)] = df_daily.loc[
                start_date:end_date, "temperature"
            ].mean()

        prolonged_anomaly_temperatures_str = "Temperature during prolonged anomalies (°C): " + ", ".join(
            [
                f"[{start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}: {temperature:.2f}]"
                for (start_date, end_date), temperature in prolonged_anomaly_temperatures.items()
            ]
        )

    return average_temperature_str, anomaly_temperatures_str, prolonged_anomaly_temperatures_str


def plot_weather(df):
    """Plots the weather data."""

    # resample to daily data
    df_daily = df.resample("D").mean()

    # plot temperature data
    fig = px.bar(
        df_daily,
        x=df_daily.index,
        y="temperature",
        title="Weather Data",
        color="temperature",
        color_continuous_scale="RdBu_r",
    )
    # hide the colorbar
    fig.update_layout(coloraxis_showscale=False)
    return fig
