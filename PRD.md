# Product Requirements Document (PRD): PetroCalc AI

## 1. Executive Summary & Global Vision
PetroCalc AI is a world-class intelligent petroleum operations and subsurface engineering platform designed for multi-disciplinary asset teams (field operators, reservoir/production engineers, and asset managers). It bridges the operational divide between daily field logs and deliverability engineering by combining automated, multi-source shift log parsing with multi-tier inflow performance calculations, hybrid physics-statistical anomaly diagnostics, step-by-step engineering calculation derivations, and multi-format document reporting.

---

## 2. Design System & UX Standards

### 2.1 Color Palette
- **Primary Industrial Blue (`#1f77b4`):** Used for primary headers, navigation accents, and standard Vogel IPR curves.
- **Success Green (`#2ca02c`):** Used for healthy well states, Darcy flow models, and successful database transactions.
- **Warning Amber (`#ff7f0e`):** Used for operational drift, high water cut thresholds, and engineering review warnings.
- **Critical Crimson (`#d62728`):** Used for critical well integrity alerts (packer leaks, tubing-casing communication, sand production).
- **Surface Dark / Neutral (`#2c3e50` / `#f8fafc`):** High-contrast typography and clean card backgrounds optimized for both field-side mobile screens and engineering desktop workstations.

### 2.2 Typography & Layout
- **Font Family:** Clean sans-serif (`Inter`, `-apple-system`, `Segoe UI`, `Roboto`) for optimal readability under high-stress rig and office environments.
- **Data Tables & Equations:** Monospace typography for numerical parameters, pressure readouts, and LaTeX mathematical formulations.

---

## 3. Product Architecture & Technical Stack

- **Frontend & UI Framework:** Python Streamlit providing reactive multi-persona dashboards with zero client-side JavaScript overhead.
- **Calculation Core:** High-performance numerical libraries (`numpy`, `scipy`) for exact analytical deliverability modeling and curve intersection solvers.
- **Document Ingestion & Processing:** Deterministic local parsing engine (`pypdf`, `python-docx`, `openpyxl`, `pandas`, Regex normalization) ensuring zero third-party API dependencies or cloud latency in offline rig environments.
- **Persistence & Storage:** Dual-mode SQLite (`petrocalc.db`) for lightweight local offline workspace persistence and containerized PostgreSQL for enterprise cloud deployments.
- **Reporting Suite:** Matplotlib chart generation coupled with ReportLab (PDF) and python-docx (Word) for publication-quality engineering memos.
- **Containerization & Ops:** Docker, Docker Compose, and Caddy reverse proxy for automated TLS/HTTPS and zero-downtime deployments.

---

## 4. Multi-Phase Implementation Roadmap

### Phase 1: MVP Core Inflow & Log Parsing (Completed)
- Tier 1 Vogel IPR deliverability calculation and AOFP estimation.
- Unstructured shift note regex parser for THP, CHP, Choke, Rate, and Water Cut.
- Hybrid anomaly diagnostics rulebook (packer leaks, sand detection, liquid loading).

### Phase 2: Multi-Persona Dashboards & Document Reporting (Completed)
- Engineering Console with all 4 deliverability tiers (Vogel, Composite, Fetkovich, Nodal VLP) and step-by-step derivations.
- Operator Field View with real-time KPI metrics and active alert banners.
- Executive Asset Summary with fleet rollup capacity and health overview tables.
- One-click report generator for PDF, DOCX, XLSX, and CSV exports.

### Phase 3: Field Validation & Automated Testing Suite (Completed)
- Sample DPR datasets (`daily_production_report.csv`, `.xlsx`, `shift_handover_sample.txt`) for immediate validation.
- Unit test suite (`tests/test_deliverability.py`) covering analytical correctness and report generation.

### Phase 4: Production Containerization & Cloud-Ready Persistence (Completed)
- Dockerfile, Docker Compose stack, Caddy reverse proxy, and PostgreSQL integration.

### Phase 5: Real-Time SCADA Telemetry & IoT Sensor Ingestion (Roadmap)
- OPC-UA and MQTT protocol connectors for live wellhead telemetry streaming.
- Automated high-frequency anomaly detection against real-time pressure and rate transients.

### Phase 6: AI-Driven Production Optimization & Autonomous Well Tuning (Roadmap)
- Machine learning surrogate models for gas lift allocation and artificial lift optimization.
- Reinforcement learning agents recommending optimal choke adjustments to maximize net present value (NPV).

### Phase 7: Multi-Asset Enterprise Cloud Synchronization & RBAC (Roadmap)
- Multi-tenant cloud architecture with Role-Based Access Control (RBAC).
- Real-time offline-first synchronization mirroring local edge databases to centralized asset clouds.

---

## 5. Agent Steering Decisions & Tool Implementation Notes
- **Steered Decision:** Implemented local deterministic document parsers instead of cloud-dependent OCR to guarantee zero downtime and data sovereignty in remote oilfield locations.
- **Modular Calculations:** Separated mathematical physics models (`calculations/ipr.py`) from presentation logic (`app.py`), enabling rigorous unit testing and verifiable engineering traceability.
