# streamlit_app.py

import streamlit as st
import pandas as pd
import plotly.express as px
import io
from datetime import datetime

st.title("PBS 3L Report Viewer")

uploaded_file = st.file_uploader("Upload your PBS 3L report CSV", type="csv")

if uploaded_file is not None:

    df = pd.read_csv(uploaded_file)

    # ---- Experiment Name Input ----
    experiment_name = st.text_input(
        "Report ID:",
        value="enter a report ID"
    )

    # ---- Tidy automatically ----
    tidy_list = []
    for col in df.columns:
        if col.endswith(".1"):
            continue
        value_col = f"{col}.1"
        if value_col in df.columns:
            temp = df[[col, value_col]].dropna()
            temp.columns = ["time", "value"]
            temp["variable"] = col
            temp["time"] = temp["time"].astype(str).str.strip()
            temp["time"] = pd.to_datetime(temp["time"], format="%m/%d/%Y%I:%M:%S%p")
            # temp["time"] = pd.to_datetime(temp["time"])
            tidy_list.append(temp)

    tidy = pd.concat(tidy_list, ignore_index=True).sort_values("time")

    all_vars = tidy["variable"].unique().tolist()
    default_vars= ['pHPV', 'DOPV(%)', 'pHCO2User(%)', 'MainGasUser(LPM)', 'TempPV(C)', 'LevelPV(L)', 'AgSP(RPM)']

    selected_vars = st.multiselect(
        "Select variables to plot",
        all_vars,
        default= default_vars
    )

    if selected_vars:

        plot_df = tidy.query("variable in @selected_vars")

        fig = px.line(
            plot_df,
            x="time",
            y="value",
            facet_row="variable",
            height=300 * len(selected_vars),
            title=experiment_name
        )

        fig.update_yaxes(matches=None)
        fig.update_xaxes(matches="x")
        fig.update_layout(showlegend=False)

        st.plotly_chart(fig, use_container_width=True)

        # -------- File naming --------
        safe_name = experiment_name.replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")

        # -------- HTML Download --------
        html_buffer = io.StringIO()
        fig.write_html(html_buffer, full_html=True)

        st.download_button(
            label="Download Interactive HTML",
            data=html_buffer.getvalue(),
            file_name=f"{safe_name}_{timestamp}.html",
            mime="text/html"
        )

        # -------- PDF Download --------
        pdf_buffer = io.BytesIO()
        fig.write_image(pdf_buffer, format="pdf")

        st.download_button(
            label="Download PDF",
            data=pdf_buffer.getvalue(),
            file_name=f"{safe_name}_{timestamp}.pdf",
            mime="application/pdf"
        )
