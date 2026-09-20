import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json

from calculations.ipr import (
    calculate_vogel_qmax,
    generate_vogel_curve,
    generate_composite_curve,
    generate_fetkovich_curve,
    generate_nodal_analysis,
    calculate_productivity_index,
    explain_ipr_derivation
)
from parser.log_parser import parse_shift_note
from diagnostics.anomaly_engine import detect_anomalies
from database.db import (
    init_db,
    save_shift_log,
    get_shift_history,
    save_ipr_test,
    get_ipr_history
)
from utils.document_io import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_df_from_excel_or_csv,
    generate_word_report,
    generate_pdf_report,
    generate_excel_workbook
)

# Initialize Database
init_db()

# Page configuration
st.set_page_config(
    page_title="PetroCalc AI",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App Title Header
st.title("PetroCalc AI — Petroleum Engineering & Operations Platform")
st.markdown("---")

# --- Sidebar Persona & Demo Loader ---
st.sidebar.title("Persona & Navigation")
persona = st.sidebar.selectbox(
    "Dashboard Persona",
    ["Engineering Console", "Operator Field View", "Executive Asset Summary"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Demo Ingestion")
if st.sidebar.button("📥 Load Sample DPR Data"):
    try:
        # Load sample CSV
        demo_df = pd.read_csv("sample_data/daily_production_report.csv")
        for _, row in demo_df.iterrows():
            w_name = str(row["Well"])
            p_data = {
                "thp": float(row["THP"]),
                "chp": float(row["CHP"]),
                "choke_size": float(row["Choke"]),
                "liquid_rate": float(row["Rate"]),
                "water_cut": float(row["WaterCut"]),
                "raw_text": f"Sample DPR import for {w_name} on {row['Date']}",
                "keywords": ["sand"] if w_name == "Well-02" else []
            }
            anoms = detect_anomalies(p_data)
            save_shift_log(w_name, p_data, anoms)
            # Also seed an IPR test record
            save_ipr_test(w_name, "Tier 1: Baseline Vogel", 3500.0, 3000.0, 2000.0, float(row["Rate"]), float(row["Rate"]) * 2.1, 0.85)
        st.sidebar.success("Successfully loaded sample demo data across 5 wells!")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error loading sample data: {e}")

if persona == "Engineering Console":
    page = st.sidebar.radio("Select Module", ["IPR Deliverability", "Shift Log Parser"])

    if page == "IPR Deliverability":
        st.header("Inflow Performance Relationship (IPR) & Nodal Analysis Suite")
        st.markdown("Select analytical deliverability tiers, evaluate well inflow vs. VLP outflow, view step-by-step engineering derivations, and export professional reports.")

        col1, col2 = st.columns([1, 2])

        with col1:
            st.subheader("Well & Reservoir Parameters")
            
            well_name_ipr = st.text_input("Well Name / Identifier", value="Well-02")

            analysis_mode = st.selectbox(
                "Deliverability Model / Mode",
                [
                    "Tier 1: Baseline Vogel",
                    "Tier 2: Composite Vogel (P_R > P_b)",
                    "Tier 3: Fetkovich Backpressure",
                    "Tier 4: Nodal System Analysis (IPR vs VLP Tubing Curve)",
                    "Model Comparison Overlay (All curves on one Plotly chart)"
                ]
            )

            p_r = st.number_input("Reservoir Pressure (P_R, psi)", min_value=100.0, max_value=10000.0, value=3500.0, step=50.0)
            pwf_test = st.number_input("Test Flowing Pressure (P_wf,test, psi)", min_value=0.0, max_value=10000.0, value=2000.0, step=50.0)
            q_test = st.number_input("Test Flow Rate (q_test, STB/day)", min_value=0.1, max_value=50000.0, value=1200.0, step=50.0)

            p_b = 3000.0
            n_fet = 0.85
            p_wh = 300.0
            well_depth = 8000.0

            if "Composite" in analysis_mode or "Comparison" in analysis_mode:
                p_b = st.number_input("Bubble Point Pressure (P_b, psi)", min_value=100.0, max_value=10000.0, value=3000.0, step=50.0)

            if "Fetkovich" in analysis_mode or "Comparison" in analysis_mode:
                n_fet = st.number_input("Fetkovich Exponent (n)", min_value=0.5, max_value=1.0, value=0.85, step=0.05)

            if "Nodal" in analysis_mode:
                p_wh = st.number_input("Tubing Head Pressure (P_wh, psi)", min_value=50.0, max_value=3000.0, value=300.0, step=25.0)
                well_depth = st.number_input("Well True Vertical Depth (TVD, ft)", min_value=1000.0, max_value=25000.0, value=8000.0, step=250.0)

            calc_button = st.button("Calculate & Plot Deliverability", type="primary")

        with col2:
            if calc_button:
                if pwf_test >= p_r:
                    st.error("Error: Test Flowing Pressure (P_wf) must be less than Reservoir Pressure (P_R).")
                else:
                    q_max = calculate_vogel_qmax(q_test, pwf_test, p_r)
                    j_index = calculate_productivity_index(q_test, pwf_test, p_r)

                    if st.button("💾 Save Well Test Record to Database"):
                        save_ipr_test(well_name_ipr, analysis_mode, p_r, p_b, pwf_test, q_test, q_max, j_index)
                        st.success(f"Successfully saved test record for {well_name_ipr}!")

                    if analysis_mode == "Tier 1: Baseline Vogel":
                        df_curve = generate_vogel_curve(q_max, p_r)
                        res_dict = {"Max Oil Rate / AOFP": f"{q_max:,.1f} STB/d", "Productivity Index (J)": f"{j_index:,.2f} STB/d/psi"}
                    elif analysis_mode == "Tier 2: Composite Vogel (P_R > P_b)":
                        df_curve = generate_composite_curve(p_r, p_b, j_index)
                        res_dict = {"Estimated AOFP": f"{q_max:,.1f} STB/d", "Productivity Index (J)": f"{j_index:,.2f} STB/d/psi"}
                    elif analysis_mode == "Tier 3: Fetkovich Backpressure":
                        df_curve = generate_fetkovich_curve(p_r, q_test, pwf_test, n_fet)
                        res_dict = {"Fetkovich Exponent (n)": f"{n_fet}", "Productivity Index (J)": f"{j_index:,.2f} STB/d/psi"}
                    elif analysis_mode == "Tier 4: Nodal System Analysis (IPR vs VLP Tubing Curve)":
                        nodal_res = generate_nodal_analysis(p_r, q_max, p_wh, well_depth)
                        df_curve = nodal_res["ipr_df"]
                        res_dict = {"Operating Flow Rate (q_oper)": f"{nodal_res['q_oper']:,.1f} STB/d", "Operating P_wf": f"{nodal_res['pwf_oper']:,.1f} psi"}
                    else:
                        df_curve = generate_vogel_curve(q_max, p_r)
                        res_dict = {"Baseline Vogel AOFP": f"{q_max:,.1f} STB/d", "Productivity Index (J)": f"{j_index:,.2f} STB/d/psi"}

                    m1, m2 = st.columns(2)
                    for i, (k, v) in enumerate(res_dict.items()):
                        if i == 0:
                            with m1: st.metric(label=k, value=v)
                        else:
                            with m2: st.metric(label=k, value=v)

                    fig = go.Figure()
                    if analysis_mode == "Model Comparison Overlay (All curves on one Plotly chart)":
                        df_v = generate_vogel_curve(q_max, p_r)
                        df_c = generate_composite_curve(p_r, p_b, j_index)
                        df_f = generate_fetkovich_curve(p_r, q_test, pwf_test, n_fet)
                        fig.add_trace(go.Scatter(x=df_v["Qo"], y=df_v["Pwf"], mode="lines", name="Tier 1: Vogel", line=dict(color="#1f77b4", width=3)))
                        fig.add_trace(go.Scatter(x=df_c["Qo"], y=df_c["Pwf"], mode="lines", name="Tier 2: Composite", line=dict(color="#2ca02c", width=3, dash="dash")))
                        fig.add_trace(go.Scatter(x=df_f["Qo"], y=df_f["Pwf"], mode="lines", name=f"Tier 3: Fetkovich (n={n_fet})", line=dict(color="#ff7f0e", width=3, dash="dot")))
                    elif analysis_mode == "Tier 4: Nodal System Analysis (IPR vs VLP Tubing Curve)":
                        nodal_res = generate_nodal_analysis(p_r, q_max, p_wh, well_depth)
                        fig.add_trace(go.Scatter(x=nodal_res["ipr_df"]["Qo"], y=nodal_res["ipr_df"]["Pwf"], mode="lines", name="Reservoir Inflow (IPR)", line=dict(color="#1f77b4", width=3)))
                        fig.add_trace(go.Scatter(x=nodal_res["vlp_df"]["Qo"], y=nodal_res["vlp_df"]["Pwf"], mode="lines", name="Tubing Outflow (VLP)", line=dict(color="#d62728", width=3)))
                        fig.add_trace(go.Scatter(x=[nodal_res["q_oper"]], y=[nodal_res["pwf_oper"]], mode="markers+text", name="Operating Point", text=[f"Operating Point<br>({nodal_res['q_oper']:,.1f} STB/d)"], textposition="top center", marker=dict(color="purple", size=14, symbol="star")))
                    else:
                        fig.add_trace(go.Scatter(x=df_curve["Qo"], y=df_curve["Pwf"], mode="lines", name=analysis_mode, line=dict(color="#1f77b4", width=3)))
                        fig.add_trace(go.Scatter(x=[q_test], y=[pwf_test], mode="markers+text", name="Test Point", text=[f"Test ({q_test} STB/d)"], textposition="top right", marker=dict(color="red", size=12, symbol="diamond")))

                    fig.update_layout(title=f"Deliverability Curve — {analysis_mode}", xaxis_title="Flow Rate, q_o (STB/day)", yaxis_title="Pressure, P (psi)", template="plotly_white", height=450)
                    st.plotly_chart(fig, use_container_width=True)

                    derivation_markdown = explain_ipr_derivation(analysis_mode, p_r, pwf_test, q_test, p_b, n_fet, None, j_index, q_max)
                    with st.expander("📐 Step-by-Step Engineering Calculation & Derivation", expanded=False):
                        st.markdown(derivation_markdown)

                    st.markdown("### 📥 Export Deliverability Report")
                    inputs_dict = {"Reservoir Pressure (psi)": p_r, "Test Pwf (psi)": pwf_test, "Test Rate (STB/d)": q_test, "Bubble Point (psi)": p_b, "Fetkovich n": n_fet}
                    
                    d_col1, d_col2, d_col3, d_col4 = st.columns(4)
                    with d_col1:
                        pdf_bytes = generate_pdf_report(well_name_ipr, analysis_mode, inputs_dict, res_dict, derivation_markdown, df_curve)
                        st.download_button("Download PDF", data=pdf_bytes, file_name=f"{well_name_ipr}_Deliverability_Report.pdf", mime="application/pdf")
                    with d_col2:
                        docx_bytes = generate_word_report(well_name_ipr, analysis_mode, inputs_dict, res_dict, derivation_markdown, df_curve)
                        st.download_button("Download DOCX", data=docx_bytes, file_name=f"{well_name_ipr}_Engineering_Memo.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                    with d_col3:
                        xlsx_bytes = generate_excel_workbook(inputs_dict, res_dict, df_curve)
                        st.download_button("Download XLSX", data=xlsx_bytes, file_name=f"{well_name_ipr}_Calculation_Workbook.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    with d_col4:
                        csv_bytes = df_curve.to_csv(index=False).encode('utf-8')
                        st.download_button("Download CSV", data=csv_bytes, file_name=f"{well_name_ipr}_Curve_Coordinates.csv", mime="text/csv")
            else:
                st.info("👈 Enter well parameters in the sidebar and click **Calculate & Plot Deliverability** to run deliverability models.")

        st.markdown("---")
        st.subheader("📚 Saved Well Test & Deliverability Records")
        ipr_history_df = get_ipr_history()
        if ipr_history_df.empty:
            st.info("No saved IPR records found in database.")
        else:
            st.dataframe(ipr_history_df, use_container_width=True)

    elif page == "Shift Log Parser":
        st.header("Omni-Channel Shift Log Parser & Diagnostics")
        st.markdown("Upload multi-format documents (PDF, DOCX, Excel, CSV, TXT) or paste unstructured shift reports to extract parameters, trigger anomalies, and record data.")

        tab1, tab2 = st.tabs(["Multi-Format File / Note Parser", "Batch CSV / Spreadsheet Upload & History"])

        with tab1:
            well_name_shift = st.text_input("Well Name / Identifier", value="Well-02")
            uploaded_doc = st.file_uploader("Upload Shift Report / Handover Document", type=['csv', 'xlsx', 'xls', 'docx', 'pdf', 'txt'])
            
            extracted_text = ""
            if uploaded_doc is not None:
                fname = uploaded_doc.name.lower()
                if fname.endswith('.pdf'):
                    extracted_text = extract_text_from_pdf(uploaded_doc)
                elif fname.endswith('.docx'):
                    extracted_text = extract_text_from_docx(uploaded_doc)
                elif fname.endswith(('.xlsx', '.xls', '.csv')):
                    df_temp = extract_df_from_excel_or_csv(uploaded_doc, fname)
                    extracted_text = df_temp.to_string()
                elif fname.endswith('.txt'):
                    extracted_text = uploaded_doc.read().decode('utf-8', errors='ignore')

            # Default sample report or loaded sample text
            default_report = (
                "Well-02 morning report: Choke adjusted to 36/64. "
                "Tubing head pressure (THP) down to 780 psi from 920 psi. "
                "Casing head pressure (CHP) noted at 800 psi. "
                "Liquid rate recorded at 380 bopd with BS&W water cut spiking to 72%. "
                "Intermittent liquid slugging and minor sand production observed during high-rate testing."
            )

            shift_text = st.text_area("Field Shift Report / Handover Notes (or extracted text)", value=extracted_text if extracted_text else default_report, height=180)

            if st.button("Parse Log & Analyze Anomalies", type="primary"):
                parsed = parse_shift_note(shift_text)
                anomalies = detect_anomalies(parsed)

                st.session_state["last_parsed"] = parsed
                st.session_state["last_anomalies"] = anomalies
                st.session_state["last_well"] = well_name_shift

                st.markdown("### 📊 Extracted Parameters")
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1: st.metric("Tubing Pressure (THP)", f"{parsed['thp']} psi" if parsed['thp'] is not None else "N/A")
                with col2: st.metric("Casing Pressure (CHP)", f"{parsed['chp']} psi" if parsed['chp'] is not None else "N/A")
                with col3: st.metric("Choke Size", f"{parsed['choke_size']}/64\"" if parsed['choke_size'] is not None else "N/A")
                with col4: st.metric("Liquid Rate", f"{parsed['liquid_rate']} bopd" if parsed['liquid_rate'] is not None else "N/A")
                with col5: st.metric("Water Cut (BS&W)", f"{parsed['water_cut']}%" if parsed['water_cut'] is not None else "N/A")

                if parsed['keywords']:
                    st.markdown(f"**Detected Keywords / Events:** {', '.join([f'`{k}`' for k in parsed['keywords']])}")

                st.markdown("---")
                st.markdown("### 🔍 Hybrid Anomaly Diagnostics & Alerts")

                if not anomalies:
                    st.success("No critical or warning anomalies detected. Well operating within normal parameters.")
                else:
                    for alert in anomalies:
                        if alert["severity"] == "Critical":
                            st.error(f"🔴 **CRITICAL ALERT: {alert['title']}**\n\n{alert['description']}")
                        elif alert["severity"] == "Warning":
                            st.warning(f"🟡 **WARNING: {alert['title']}**\n\n{alert['description']}")
                        else:
                            st.info(f"🔵 **INFO: {alert['title']}**\n\n{alert['description']}")

            if "last_parsed" in st.session_state:
                if st.button("💾 Save Parsed Log & Alerts to Database"):
                    save_shift_log(st.session_state["last_well"], st.session_state["last_parsed"], st.session_state["last_anomalies"])
                    st.success("Successfully saved shift log and anomalies to database!")

        with tab2:
            st.subheader("Batch Daily Production Report (DPR) Upload")
            uploaded_batch = st.file_uploader("Choose a spreadsheet or CSV file", type=['csv', 'xlsx', 'xls'])
            if uploaded_batch is not None:
                try:
                    batch_df = extract_df_from_excel_or_csv(uploaded_batch, uploaded_batch.name.lower())
                    st.success(f"Successfully loaded {len(batch_df)} rows!")
                    st.dataframe(batch_df, use_container_width=True)

                    if st.button("Import Batch Records to Database"):
                        for _, row in batch_df.iterrows():
                            w_name = str(row.get("Well", row.get("well", "Unknown")))
                            p_data = {
                                "thp": float(row.get("THP", row.get("thp", 0.0))),
                                "chp": float(row.get("CHP", row.get("chp", 0.0))),
                                "choke_size": float(row.get("Choke", row.get("choke", 0.0))),
                                "liquid_rate": float(row.get("Rate", row.get("rate", 0.0))),
                                "water_cut": float(row.get("WaterCut", row.get("water_cut", 0.0))),
                                "raw_text": f"Batch Spreadsheet Import for {w_name}",
                                "keywords": []
                            }
                            anoms = detect_anomalies(p_data)
                            save_shift_log(w_name, p_data, anoms)
                        st.success("Batch records imported successfully!")
                except Exception as e:
                    st.error(f"Error parsing spreadsheet: {e}")

            st.markdown("---")
            st.subheader("📚 Historical Shift Records (SQLite)")
            history_df = get_shift_history()
            if history_df.empty:
                st.info("No saved shift logs found in database.")
            else:
                st.dataframe(history_df, use_container_width=True)

elif persona == "Operator Field View":
    st.header("🛢️ Operator Field View & Real-Time Monitoring")
    st.markdown("Quick operational telemetry, real-time anomaly alerts, and fast handover logging.")

    shift_history = get_shift_history()
    available_wells = ["Well-01", "Well-02", "Well-03", "Well-04", "Well-05"]
    if not shift_history.empty and "well_name" in shift_history.columns:
        db_wells = shift_history["well_name"].dropna().unique().tolist()
        available_wells = sorted(list(set(available_wells + db_wells)))

    selected_well = st.selectbox("Select Monitored Well", available_wells)

    latest_log = None
    if not shift_history.empty:
        well_logs = shift_history[shift_history["well_name"] == selected_well]
        if not well_logs.empty:
            latest_log = well_logs.iloc[0]

    # Top Alert Banner for Critical Anomalies
    if latest_log is not None and latest_log.get("anomalies_json"):
        try:
            anoms = json.loads(latest_log["anomalies_json"])
            for a in anoms:
                if a.get("severity") == "Critical":
                    st.error(f"🚨 **CRITICAL ALERT ({selected_well}): {a.get('title')}** — {a.get('description')}")
        except Exception:
            pass

    # 4-Column Operational KPI Metrics
    thp_val = latest_log["thp"] if latest_log is not None and pd.notna(latest_log.get("thp")) else 780.0
    chp_val = latest_log["chp"] if latest_log is not None and pd.notna(latest_log.get("chp")) else 800.0
    choke_val = latest_log["choke"] if latest_log is not None and pd.notna(latest_log.get("choke")) else 36.0
    rate_val = latest_log["liquid_rate"] if latest_log is not None and pd.notna(latest_log.get("liquid_rate")) else 380.0
    wcut_val = latest_log["water_cut"] if latest_log is not None and pd.notna(latest_log.get("water_cut")) else 72.0

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1: st.metric("Tubing Pressure (THP)", f"{thp_val:,.1f} psi")
    with kpi2: st.metric("Casing Pressure (CHP)", f"{chp_val:,.1f} psi")
    with kpi3: st.metric("Choke Setting", f"{choke_val:,.1f}/64\"")
    with kpi4: st.metric("Liquid Flow Rate", f"{rate_val:,.1f} bopd", delta=f"Water Cut: {wcut_val}%")

    st.markdown("---")
    st.subheader("⚡ Quick Field Handover Note Parser")
    st.markdown("Paste new shift observations to instantly evaluate well integrity and trigger operational alerts.")

    quick_text = st.text_area("Handover Observation", value=f"{selected_well} update: Choke at {choke_val}/64\", THP at {thp_val} psi, CHP at {chp_val} psi, rate {rate_val} bopd, BS&W water cut {wcut_val}%.", height=120)

    if st.button("Quick Evaluate & Log", type="primary"):
        parsed_q = parse_shift_note(quick_text)
        anoms_q = detect_anomalies(parsed_q)
        save_shift_log(selected_well, parsed_q, anoms_q)
        st.success(f"Shift log successfully recorded for {selected_well}!")

        if not anoms_q:
            st.success("No critical anomalies detected. Well operating normally.")
        else:
            for alert in anoms_q:
                if alert["severity"] == "Critical":
                    st.error(f"🔴 **{alert['title']}**: {alert['description']}")
                elif alert["severity"] == "Warning":
                    st.warning(f"🟡 **{alert['title']}**: {alert['description']}")
                else:
                    st.info(f"🔵 **{alert['title']}**: {alert['description']}")

elif persona == "Executive Asset Summary":
    st.header("📈 Executive Asset Summary & Portfolio Health")
    st.markdown("High-level asset deliverability health, aggregate production figures, and critical alert rollups across all monitored fields.")

    ipr_df = get_ipr_history()
    shift_df = get_shift_history()

    total_wells = 5
    if not shift_df.empty and "well_name" in shift_df.columns:
        total_wells = shift_df["well_name"].nunique()
    elif not ipr_df.empty and "well_name" in ipr_df.columns:
        total_wells = ipr_df["well_name"].nunique()

    total_capacity = 12500.0
    if not ipr_df.empty and "q_max" in ipr_df.columns:
        latest_ipr = ipr_df.drop_duplicates(subset=["well_name"], keep="first")
        total_capacity = latest_ipr["q_max"].sum()

    critical_count = 0
    if not shift_df.empty and "anomalies_json" in shift_df.columns:
        for _, row in shift_df.iterrows():
            try:
                anoms = json.loads(row["anomalies_json"])
                for a in anoms:
                    if a.get("severity") == "Critical":
                        critical_count += 1
            except Exception:
                pass

    # Rollup KPI Cards
    ex1, ex2, ex3 = st.columns(3)
    with ex1: st.metric("Total Monitored Wells", f"{total_wells}")
    with ex2: st.metric("Total Asset Deliverability Capacity", f"{total_capacity:,.1f} STB/d")
    with ex3: st.metric("Active Critical Incidents", f"{critical_count}", delta_color="inverse")

    st.markdown("---")
    st.subheader("🛡️ Asset Health & Integrity Overview Table")

    if ipr_df.empty and shift_df.empty:
        st.info("No recorded well test or shift data available in database. Click **📥 Load Sample DPR Data** in the sidebar to populate demo records.")
    else:
        wells_list = set()
        if not ipr_df.empty: wells_list.update(ipr_df["well_name"].dropna().unique())
        if not shift_df.empty: wells_list.update(shift_df["well_name"].dropna().unique())

        summary_rows = []
        for w in wells_list:
            w_ipr = ipr_df[ipr_df["well_name"] == w] if not ipr_df.empty else pd.DataFrame()
            w_shift = shift_df[shift_df["well_name"] == w] if not shift_df.empty else pd.DataFrame()

            model = w_ipr.iloc[0]["model_type"] if not w_ipr.empty else "Standard Vogel"
            test_date = w_ipr.iloc[0]["timestamp"] if not w_ipr.empty else (w_shift.iloc[0]["timestamp"] if not w_shift.empty else "N/A")
            qmax = w_ipr.iloc[0]["q_max"] if not w_ipr.empty else 2500.0
            wcut = w_shift.iloc[0]["water_cut"] if not w_shift.empty else 20.0

            status = "Normal"
            if not w_shift.empty:
                try:
                    anoms = json.loads(w_shift.iloc[0]["anomalies_json"])
                    for a in anoms:
                        if a.get("severity") == "Critical": status = "Critical"
                        elif a.get("severity") == "Warning" and status != "Critical": status = "Warning"
                except Exception:
                    pass

            summary_rows.append({
                "Well Name": w,
                "Latest Activity": test_date,
                "Model Used": model,
                "AOFP (STB/d)": f"{qmax:,.1f}",
                "Water Cut (%)": f"{wcut}%",
                "Integrity Status": status
            })

        summary_table_df = pd.DataFrame(summary_rows)
        st.dataframe(summary_table_df, use_container_width=True)

        if not ipr_df.empty:
            chart_df = ipr_df.drop_duplicates(subset=["well_name"], keep="first")
            fig_bar = go.Figure(go.Bar(
                x=chart_df["well_name"],
                y=chart_df["q_max"],
                marker_color="#1f77b4"
            ))
            fig_bar.update_layout(
                title="AOFP Capacity Distribution per Well",
                xaxis_title="Well Name",
                yaxis_title="Max Oil Rate / AOFP (STB/day)",
                template="plotly_white",
                height=400
            )
            st.plotly_chart(fig_bar, use_container_width=True)

# Footer instructions
st.sidebar.markdown("---")
st.sidebar.markdown("### How to Run Locally")
st.sidebar.code("pip install -r requirements.txt\nstreamlit run app.py")
