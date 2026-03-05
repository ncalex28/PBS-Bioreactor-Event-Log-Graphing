import streamlit as st
import pandas as pd
import plotly.express as px
import io
from datetime import datetime

st.title("PBS 3L Report Viewer")

uploaded_file = st.file_uploader("Upload your PBS 3L report CSV", type="csv")

# -------- PBS PARSER --------
def parse_pbs_csv(file):

    df = pd.read_csv(file)

    # remove blank columns
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    # clean column names
    df.columns = df.columns.str.strip()

    # remove metadata columns
    metadata_terms = [
        "Report", "Batch", "Generated",
        "Records", "Description", "ReportID"
    ]

    df = df.loc[:, ~df.columns.str.contains("|".join(metadata_terms), case=False)]

    cols = list(df.columns)

    parsed = []

    for i in range(0, len(cols) - 1, 2):

        time_col = cols[i]
        value_col = cols[i + 1]

        temp = pd.DataFrame({
            "time": pd.to_datetime(df[time_col], errors="coerce"),
            "value": pd.to_numeric(df[value_col], errors="coerce"),
            "variable": value_col
        })

        temp = temp.dropna(subset=["time"])

        parsed.append(temp)

    tidy = pd.concat(parsed, ignore_index=True)

    return tidy


if uploaded_file is not None:

    tidy = parse_pbs_csv(uploaded_file)

    # ---- Experiment Name ----
    experiment_name = st.text_input(
        "Report ID:",
        value="enter a report ID"
    )

    all_vars = sorted(tidy["variable"].unique().tolist())

    default_vars = [
        'pHPV',
        'DOPV(%)',
        'pHCO2User(%)',
        'MainGasUser(LPM)',
        'TempPV(C)',
        'LevelPV(L)',
        'AgSP(RPM)'
    ]

    # -------- Subsystem Detection --------
    agitation_vars = [v for v in all_vars if "Ag" in v]
    do_vars = [v for v in all_vars if "DO" in v]
    ph_vars = [v for v in all_vars if "pH" in v]
    temp_vars = [v for v in all_vars if "Temp" in v]
    gas_vars = [v for v in all_vars if "Gas" in v or "Flow" in v or "MFC" in v]
    level_vars = [v for v in all_vars if "Level" in v]

    # -------- Tabs --------
    tab_selected, tab_ag, tab_do, tab_ph, tab_temp, tab_gas, tab_level = st.tabs([
        "Selected Variables",
        "Agitation",
        "DO",
        "pH",
        "Temperature",
        "Gas Flow",
        "Level"
    ])

    def plot_section(var_list):

        if not var_list:
            st.write("No variables found.")
            return None

        plot_df = tidy.query("variable in @var_list")

        fig = px.line(
            plot_df,
            x="time",
            y="value",
            facet_row="variable",
            height=300 * len(var_list),
            title=experiment_name
        )

        fig.update_yaxes(matches=None)
        fig.update_xaxes(matches="x")
        fig.update_layout(showlegend=False)

        st.plotly_chart(fig, use_container_width=True)

        return fig


    # -------- Selected Variables Tab --------
    with tab_selected:

        selected_vars = st.multiselect(
            "Select variables to plot",
            all_vars,
            default=[v for v in default_vars if v in all_vars]
        )

        fig = None

        if selected_vars:
            fig = plot_section(selected_vars)

        if fig:

            safe_name = experiment_name.replace(" ", "_")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")

            # HTML
            html_buffer = io.StringIO()
            fig.write_html(html_buffer, full_html=True)

            st.download_button(
                label="Download Interactive HTML",
                data=html_buffer.getvalue(),
                file_name=f"{safe_name}_{timestamp}.html",
                mime="text/html"
            )

            # PDF
            pdf_buffer = io.BytesIO()
            fig.write_image(pdf_buffer, format="pdf")

            st.download_button(
                label="Download PDF",
                data=pdf_buffer.getvalue(),
                file_name=f"{safe_name}_{timestamp}.pdf",
                mime="application/pdf"
            )


    with tab_ag:
        plot_section(agitation_vars)

    with tab_do:
        plot_section(do_vars)

    with tab_ph:
        plot_section(ph_vars)

    with tab_temp:
        plot_section(temp_vars)

    with tab_gas:
        plot_section(gas_vars)

    with tab_level:
        plot_section(level_vars)
