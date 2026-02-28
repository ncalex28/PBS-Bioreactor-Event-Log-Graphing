# streamlit_app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import io

st.title("Bioreactor Data Viewer")

uploaded_file = st.file_uploader("Upload your reactor CSV", type="csv")

if uploaded_file is not None:

    df = pd.read_csv(uploaded_file)

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
            temp["time"] = pd.to_datetime(temp["time"])
            tidy_list.append(temp)

    tidy = pd.concat(tidy_list, ignore_index=True).sort_values("time")

    st.success("Data tidied successfully!")

    # ---- Variable selection ----
    all_vars = tidy["variable"].unique().tolist()

    selected_vars = st.multiselect(
        "Select variables to plot",
        all_vars,
        default=all_vars[:5]
    )

    if selected_vars:

        plot_df = tidy.query("variable in @selected_vars")

        fig = px.line(
            plot_df,
            x="time",
            y="value",
            facet_row="variable",
            height=300 * len(selected_vars)
        )

        fig.update_yaxes(matches=None)
        fig.update_xaxes(matches="x")
        fig.update_layout(showlegend=False)

        st.plotly_chart(fig, use_container_width=True)

        # ---- HTML export ----
        html_buffer = io.StringIO()
        fig.write_html(html_buffer, full_html=True)

        st.download_button(
            label="Download Interactive HTML",
            data=html_buffer.getvalue(),
            file_name="bioreactor_plot.html",
            mime="text/html"
        )
