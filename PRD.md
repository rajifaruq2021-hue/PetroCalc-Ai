# Product Requirements Document (PRD): PetroCalc AI

## 1. Executive Summary & Vision
PetroCalc AI is an intelligent petroleum operations and subsurface engineering platform designed for multi-disciplinary asset teams (field operators, reservoir/production engineers, and asset managers). It bridges the operational divide between daily field logs and deliverability engineering by combining automated, multi-source shift log parsing with multi-tier inflow performance calculations and hybrid physics-statistical anomaly diagnostics.

---

## 2. Target Personas & Core Workflows

### 2.1 Personas
* **Field Operators & Well Technicians:** Log daily shifts quickly, capture downhole and surface metrics across varied input formats, and receive immediate alerts on anomalous well behavior.
* **Production & Reservoir Engineers:** Model single- and multi-phase inflow curves, evaluate well deliverability at varying depletion states, and calibrate operating envelopes.
* **Asset Leads & Engineering Managers:** Review high-level asset health summaries, track parameter shifts across operational handovers, and export standardized reports.

### 2.2 Core Workflow
1. **Field Data Ingestion:** Input data via unstructured free text, tabular spreadsheets (.csv, .xlsx), PDF morning handovers, or voice dictation.
2. **Extraction & Normalization Engine:** Extract key parameters and allow side-by-side reconciliation against source documents.
3. **Cross-Shift Parameter Tracking:** Correlate extracted readings across consecutive shifts to identify trend shifts.
4. **Hybrid Anomaly Diagnostics:** Evaluate data against physics rules and statistical trend models to flag real-time alerts.
5. **Multi-Tier Inflow Performance Engine:** Compute reservoir deliverability curves using selectable analytical complexities.
6. **Multi-Persona Dashboard & Reporting:** Visualize interactive plots tailored to user roles and export one-click reports (PDF, CSV, JSON).

---

## 3. Product Architecture & Feature Requirements

### 3.1 Inflow Performance Relationship (IPR) Engine
The deliverability suite supports selectable analytical complexities, allowing engineers to switch models depending on fluid characteristics and available test data:

* **Tier 1: Baseline Vogel Formulation**
  * Models saturated two-phase solution-gas drive reservoirs where reservoir pressure is at or below bubble point ($P_R \le P_b$).
  * Dynamic calculation of Maximum Oil Rate / Absolute Open Flow Potential ($q_{o,\max}$) and generation of flow rate vs. bottom-hole flowing pressure ($q_o$ vs. $P_{wf}$) curves.
* **Tier 2: Generalized Composite Inflow**
  * Handles reservoirs operating above initial bubble point pressure ($P_R > P_b$).
  * Couples straight-line Darcy flow for $P_{wf} \ge P_b$ with Vogel's quadratic relationship for $P_{wf} < P_b$.
  * Automatically resolves the Productivity Index ($J$) across both regimes.
* **Tier 3: Multi-Method Empirical Screening**
  * Incorporates Fetkovich and Jones-Blount-Glaze (JBG) deliverability formulations for high-rate, turbulence-dominated, or gas-bearing completions.
  * Side-by-side sensitivity comparisons across models.
* **Tier 4: System Nodal Integration**
  * Intersects reservoir inflow curves with Vertical Lift Performance (VLP) tubing hydraulics to establish the operating point ($q_{oper}, P_{wf,oper}$).

### 3.2 Omni-Channel Field Log Ingestion & Extraction Engine
* **Multi-Modal Data Intake:**
  * **Unstructured Text:** Natural language paste area for shift narratives, choke adjustments, and wellhead notes.
  * **Tabular Spreadsheets:** Drag-and-drop ingestion of daily production report (DPR) `.csv` and `.xlsx` files.
  * **Report Ingestion:** Document parsing for standard PDF morning handover summaries.
  * **Voice Dictation:** Speech-to-text input pipeline for field-side mobile handovers.
* **Structured Parameter Normalization:**
  * Extracts key operating parameters: Wellhead Tubing Pressure (THP), Casing Pressure (CHP), Choke Size (/64"), Gross/Net Production Rates, Water Cut (% BS&W), and Gas-Oil Ratio (GOR).
* **Multi-Format Reconciliation Mode:**
  * Interactive split-screen view allowing teams to compare extracted values against source documents to verify extraction accuracy before saving.

### 3.3 Hybrid Anomaly Detection & Diagnostics
* **Physics & Heuristic Validation Rulebook:**
  * Evaluates cross-parameter mechanical consistency (e.g., choke opening with unexpected pressure rise, water cut spikes, liquid loading symptoms).
* **Statistical & Trend Deviation Intelligence:**
  * Tracks operational baseline metrics across historical shifts.
  * Flags rate drift, gradual skin development, or flowline obstruction before complete well shut-in occurs.
* **Severity Triaging:**
  * Categorizes anomalies into three distinct levels:
    * **Informational:** Routine shift variation within normal tolerance.
    * **Warning:** Operational drift requiring engineering review.
    * **Critical:** Immediate well integrity, equipment failure, or shut-in hazard.

### 3.4 Multi-Persona Visualization & Automated Reporting
* **Role-Tailored Dashboards:**
  * **Operator View:** Clear visual indicators, active anomaly cards, gauge readouts, and streamlined shift handover logs.
  * **Engineering View:** Multi-curve plots, sensitivity crosshairs, PVT tuning parameters, and mathematical calculation breakdowns.
  * **Executive View:** Field-wide asset deliverability health, aggregate production figures, and critical alert rollups.
* **Export & Reporting Suite:**
  * One-click generation of professional executive PDF shift reports containing current well status, active anomaly summaries, and generated IPR charts.
  * Clean exports of normalized production time-series into standard `.csv` and `.json` formats.

### 3.5 Data Persistence & Storage Architecture
* **Phase 1 (MVP - Local Workspace Persistence):**
  * Embedded local database (SQLite/Local JSON Store) within the application workspace.
  * Retains shift history, well test benchmarks, and diagnostic logs across sessions with zero cloud account dependencies.
* **Phase 2 (Cloud Synchronization Roadmap):**
  * Seamless sync adapter designed to mirror local SQLite records to centralized team repositories when network connectivity is available, supporting remote field site operations.

---

## 4. Acceptance Criteria & Success Metrics

1. **Calculations:** IPR curves generated by the Vogel, Composite, and Empirical modules must match analytical benchmark solutions within $<0.1\%$ error across boundary pressures ($0 \le P_{wf} \le \bar{P}_R$).
2. **Log Extraction:** Raw unstructured shift notes must correctly parse choke size, THP, and flow rate into their corresponding numerical fields with high reliability.
3. **Anomaly Flagging:** Physics rulebook must flag rapid pressure/choke discrepancies immediately upon log ingestion.
4. **Usability:** Users can switch between calculation complexities and dashboard personas with instantaneous recalculation and plot updates.
---

## 5. Agent Steering Decisions & Tool Implementation Notes

### Task 1: Architectural & Tool Choice Steering
* **Framework:** Streamlit (Python) for rapid multi-persona scientific dashboard deployment.
* **Database & Persistence:** SQLite local file database (`petrocalc.db`) with zero external cloud dependencies for Phase 1 local prototype testing.
* **Authentication:** Lightweight session-state persona selector (Operator, Engineer, Asset Manager) to test multi-role views without auth friction.
* **File Storage:** In-memory BytesIO streaming for document exports (PDF, DOCX, XLSX, CSV).
* **Steered Decision:** Shifted document parsing engine from complex external OCR services to local, deterministic parsing via `pypdf`, `python-docx`, and regex normalization. This eliminates third-party API keys and latency for offline rig environments.

### Task 2: Design Refinements Documented
* **Color Palette & Theme:** Adopted an industrial dark palette (`#0e1117` background, `#1e222b` surface cards) with safety-accent crimson (`#d9383a`) and Plotly scientific blues.
* **Typography:** Clean, legible sans-serif (`Inter`) with monospace code typography for petroleum engineering equations and parameter readouts.
* **Button & Input Styling:** High-contrast bordered inputs with clear focus states to ensure readability under field conditions.