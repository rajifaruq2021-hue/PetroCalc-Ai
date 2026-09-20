# PetroCalc AI — Petroleum Engineering Deliverability & Operations Platform

PetroCalc AI is an intelligent petroleum operations and subsurface engineering platform designed for multi-disciplinary asset teams (field operators, reservoir/production engineers, and asset managers). It bridges the operational divide between daily field logs and deliverability engineering by combining automated, multi-source shift log parsing with multi-tier inflow performance calculations, hybrid physics-statistical anomaly diagnostics, step-by-step engineering calculation derivations, and multi-format document reporting.

---

## 🚀 Executive Overview & Industry Context

Subsurface and production operations require continuous balancing between reservoir deliverability and surface/tubing network hydraulics. PetroCalc AI provides an offline-first, high-performance web application built with Streamlit and Python that automates:
- **Deliverability Modeling:** Single- and multi-phase inflow performance relationships across 4 analytical tiers.
- **Omni-Channel Field Ingestion:** Automated parameter extraction from unstructured morning handover notes, PDFs, Word memos, Excel spreadsheets, and CSV DPRs.
- **Hybrid Anomaly Diagnostics:** Real-time physics and heuristic rulebooks flagging downhole packer leaks, sand production, and liquid loading.
- **Multi-Role Dashboards:** Tailored interfaces for Engineers, Field Operators, and Asset Executives.
- **Professional Engineering Reporting:** One-click generation of PDF technical reports, Word engineering memos, and formatted Excel workbooks complete with embedded matplotlib charts and step-by-step mathematical derivations.

---

## 🏗️ Core Architecture & Persona Capabilities

1. **Engineering Console:**
   - Full IPR Deliverability suite (Tier 1 Vogel, Tier 2 Composite, Tier 3 Fetkovich, Tier 4 Nodal Analysis, and Model Comparison Overlays).
   - Expandable Step-by-Step Engineering Calculation & Derivation module detailing governing equations, pressure drawdowns, Productivity Index ($J$), and deliverability coefficients ($C$).
   - Comprehensive export suite generating PDF, DOCX, XLSX, and CSV reports.
2. **Operator Field View:**
   - Real-time telemetry monitoring (THP, CHP, Choke, Liquid Flow Rate, Water Cut %).
   - Active critical alert banners for well integrity risks (packer leaks, sand bridging).
   - Quick Field Handover Note parser for immediate conversational log evaluation.
3. **Executive Asset Summary:**
   - Fleet-wide rollup KPI cards (Total Monitored Wells, Total Deliverability Capacity, Active Critical Incidents).
   - Asset Health Overview Table summarizing well status, model used, AOFP, and water cut.
   - Comparative AOFP capacity distribution charts across all fields.

---

## ⚙️ Supported Deliverability Mathematical Formulations

- **Tier 1: Baseline Vogel Formulation** ($P_R \le P_b$)
  $$\frac{q_o}{q_{\max}} = 1 - 0.2\left(\frac{P_{wf}}{P_R}\right) - 0.8\left(\frac{P_{wf}}{P_R}\right)^2$$
- **Tier 2: Generalized Composite Inflow** ($P_R > P_b$)
  - Linear Darcy flow above bubble point ($P_{wf} \ge P_b$): $q_o = J(P_R - P_{wf})$
  - Vogel quadratic flow below bubble point ($P_{wf} < P_b$): $q_o = q_b + \frac{J \cdot P_b}{1.8}\left[1 - 0.2\left(\frac{P_{wf}}{P_b}\right) - 0.8\left(\frac{P_{wf}}{P_b}\right)^2\right]$
- **Tier 3: Fetkovich Backpressure Equation**
  $$q_o = C(P_R^2 - P_{wf}^2)^n$$
- **Tier 4: System Nodal Integration**
  - Intersects reservoir inflow (IPR) with tubing outflow (VLP) to solve operating point ($q_{\text{oper}}, P_{\text{wf},\text{oper}}$).

---

## 📋 Omni-Channel Document & Shift Log Ingestion

- **Multi-Format Intake:** Ingests `.pdf`, `.docx`, `.xlsx`, `.xls`, `.csv`, and `.txt` files.
- **Regex Parameter Normalization:** Automatically extracts Tubing Head Pressure (THP), Casing Head Pressure (CHP), Choke Size, Liquid Rate, and Water Cut (% BS&W).
- **SQLite Database Persistence:** Local workspace persistence storing shift logs, extracted anomalies, and well test records in `petrocalc.db`.

---

## 🚀 Fast-Start Local Deployment & Testing

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Run Automated Test Suite:**
   ```bash
   python -m unittest tests/test_deliverability.py
   ```
3. **Launch Streamlit App:**
   ```bash
   streamlit run app.py
   ```
   Access the web platform at `http://localhost:8501`.
