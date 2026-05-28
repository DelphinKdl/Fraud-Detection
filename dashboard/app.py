"""Streamlit dashboard for fraud detection monitoring.

Usage:
    streamlit run dashboard/app.py --server.port 8501
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st
import requests

API_URL = "http://localhost:8000"
METRICS_PATH = Path("outputs/metrics.json")

st.set_page_config(page_title="Fraud Detection Dashboard", layout="wide")
st.title("Fraud Detection Dashboard")

# --- Sidebar ---
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Model Metrics", "Live Prediction", "API Health"])

# --- Model Metrics Page ---
if page == "Model Metrics":
    st.header("Model Performance")

    if METRICS_PATH.exists():
        with open(METRICS_PATH) as f:
            metrics = json.load(f)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Precision", f"{metrics['precision']:.4f}")
        col2.metric("Recall", f"{metrics['recall']:.4f}")
        col3.metric("F1 (Fraud)", f"{metrics['f1']:.4f}")
        col4.metric("F1 (Macro)", f"{metrics['f1_macro']:.4f}")

        st.subheader("Test Set Info")
        st.write(f"- **Total samples**: {metrics['test_samples']:,}")
        st.write(f"- **Fraud samples**: {metrics['test_fraud']}")

        st.subheader("Confusion Matrix")
        cm = metrics["confusion_matrix"]
        cm_df = pd.DataFrame(
            cm,
            index=["Actual: Legit", "Actual: Fraud"],
            columns=["Pred: Legit", "Pred: Fraud"],
        )
        st.dataframe(cm_df, use_container_width=True)
    else:
        st.warning("No metrics file found. Run the pipeline first.")

# --- Live Prediction Page ---
elif page == "Live Prediction":
    st.header("Score a Transaction")
    st.write("Enter feature values to get a fraud prediction from the API.")

    with st.form("predict_form"):
        cols = st.columns(5)
        time_val = cols[0].number_input("Time", value=0.0)
        amount_val = cols[1].number_input("Amount", value=149.62)

        v_values = {}
        for i in range(1, 29):
            col_idx = (i - 1) % 5
            v_values[f"V{i}"] = cols[col_idx].number_input(f"V{i}", value=0.0, key=f"v{i}")

        submitted = st.form_submit_button("Predict")

    if submitted:
        payload = {"Time": time_val, "Amount": amount_val, **v_values}
        try:
            resp = requests.post(f"{API_URL}/predict", json=payload, timeout=10)
            if resp.status_code == 200:
                result = resp.json()
                if result["prediction"] == 1:
                    st.error(f"FRAUD DETECTED — probability: {result['probability']:.6f}")
                else:
                    st.success(f"Legitimate — probability: {result['probability']:.6f}")
            else:
                st.error(f"API error: {resp.status_code} — {resp.text}")
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to API. Start it with: `uvicorn src.api.app:app`")

# --- API Health Page ---
elif page == "API Health":
    st.header("API Health Check")

    if st.button("Check Health"):
        try:
            resp = requests.get(f"{API_URL}/health", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                st.success(f"Status: {data['status']}")
                st.write(f"- **Model loaded**: {data['model_loaded']}")
                st.write(f"- **Model version**: {data['model_version']}")
            else:
                st.error(f"API returned: {resp.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to API. Start it with: `uvicorn src.api.app:app`")
