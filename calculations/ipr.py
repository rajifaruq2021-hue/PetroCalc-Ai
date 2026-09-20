import numpy as np
import pandas as pd


def calculate_productivity_index(
    q_test: float, pwf_test: float, p_r: float
) -> float:
  """Estimates initial Productivity Index J (STB/day/psi) using drawdown at test point."""
  drawdown = p_r - pwf_test
  if drawdown <= 0:
    return 0.1
  return float(q_test / drawdown)


def calculate_vogel_qmax(q_test: float, pwf_test: float, p_r: float) -> float:
  """Calculates Absolute Open Flow Potential (AOFP / q_max) using Vogel's equation

  given a single operating test point (q_test, pwf_test) and reservoir pressure
  p_r.
  """
  if p_r <= 0 or pwf_test >= p_r:
    return float(q_test * 2.0)

  ratio = pwf_test / p_r
  denom = 1.0 - 0.2 * ratio - 0.8 * (ratio**2)

  if denom <= 0:
    return float(q_test * 2.0)

  q_max = q_test / denom
  return float(q_max)


# Alias for app.py naming compatibility
calculate_qmax_vogel = calculate_vogel_qmax


def generate_vogel_curve(
    q_max: float, p_r: float, num_points: int = 100
) -> pd.DataFrame:
  """Tier 1: Baseline Vogel IPR curve (P_R <= P_b)."""
  pwf_array = np.linspace(p_r, 0.0, num_points)
  ratio_array = pwf_array / max(p_r, 1e-5)
  qo_array = q_max * (1.0 - 0.2 * ratio_array - 0.8 * (ratio_array**2))
  qo_array = np.clip(qo_array, 0.0, None)

  return pd.DataFrame({"Pwf": pwf_array, "Qo": qo_array})


def generate_composite_curve(
    p_r: float,
    p_b: float,
    j_index: float = None,
    pwf_test: float = None,
    q_test: float = None,
    num_points: int = 100,
    **kwargs,
) -> pd.DataFrame:
  """Tier 2: Generalized Composite Inflow (P_R > P_b).

  Accepts either pre-calculated j_index OR (pwf_test, q_test) to dynamically
  compute J. Linear Darcy flow above P_b, Vogel quadratic flow below P_b.
  """
  if pwf_test is None:
    pwf_test = kwargs.get("p_wf_test", None)
  if q_test is None:
    q_test = kwargs.get("q_o_test", kwargs.get("qo_test", None))

  if j_index is None:
    if pwf_test is not None and q_test is not None:
      if pwf_test >= p_b:
        j_index = q_test / max(p_r - pwf_test, 1e-5)
      else:
        denom = (p_r - p_b) + (p_b / 1.8) * (
            1.0
            - 0.2 * (pwf_test / max(p_b, 1e-5))
            - 0.8 * ((pwf_test / max(p_b, 1e-5)) ** 2)
        )
        j_index = q_test / max(denom, 1e-5)
    else:
      j_index = 1.0

  pwf_array = np.linspace(p_r, 0.0, num_points)
  qo_array = []
  qb = j_index * max(p_r - p_b, 0.0) if p_r > p_b else 0.0

  for pwf in pwf_array:
    if p_r <= p_b:
      ratio = pwf / max(p_r, 1e-5)
      denom = max(1.0 - 0.2 * ratio - 0.8 * (ratio**2), 0.01)
      q_max = (j_index * p_r / 1.8) if j_index else (qb / denom)
      q = q_max * denom
    else:
      if pwf >= p_b:
        q = j_index * (p_r - pwf)
      else:
        ratio = pwf / max(p_b, 1e-5)
        vogel_term = max(1.0 - 0.2 * ratio - 0.8 * (ratio**2), 0.0)
        q = qb + (j_index * p_b / 1.8) * vogel_term
    qo_array.append(max(float(q), 0.0))

  return pd.DataFrame({"Pwf": pwf_array, "Qo": np.array(qo_array)})


def generate_fetkovich_curve(
    p_r: float,
    q_test: float,
    pwf_test: float = None,
    n: float = 0.85,
    num_points: int = 100,
    **kwargs,
) -> pd.DataFrame:
  """Tier 3: Fetkovich Backpressure Equation: q_o = C * (P_R^2 - P_wf^2)^n."""
  if pwf_test is None:
    pwf_test = kwargs.get("p_wf_test", p_r * 0.7)

  pwf_array = np.linspace(p_r, 0.0, num_points)
  pr2_pwf2_test = (p_r**2) - (pwf_test**2)

  if pr2_pwf2_test <= 0 or n <= 0:
    C = q_test / max(p_r - pwf_test, 1.0)
  else:
    C = q_test / (pr2_pwf2_test**n)

  qo_array = []
  for pwf in pwf_array:
    pr2_pwf2 = max((p_r**2) - (pwf**2), 0.0)
    q = C * (pr2_pwf2**n)
    qo_array.append(max(float(q), 0.0))

  return pd.DataFrame({"Pwf": pwf_array, "Qo": np.array(qo_array)})


def generate_vlp_curve(
    p_wh: float = 300.0,
    depth: float = 8000.0,
    max_rate: float = 3000.0,
    num_points: int = 100,
) -> pd.DataFrame:
  """Tier 4: Standalone VLP generator returning (Pwf, Qo) DataFrame."""
  q_array = np.linspace(0.0, max_rate, num_points)
  hydrostatic = 0.33 * depth
  friction_factor = 0.0002
  pwf_vlp = p_wh + hydrostatic + friction_factor * (q_array**2)
  return pd.DataFrame({"Pwf": pwf_vlp, "Qo": q_array})


def generate_nodal_analysis(
    p_r: float,
    q_max: float,
    p_wh: float = 300.0,
    depth: float = 8000.0,
    num_points: int = 100,
) -> dict:
  """Tier 4: System Nodal Integration (IPR vs VLP intersection).

  Returns IPR curve, VLP curve, and operating point (q_oper, pwf_oper).
  """
  ipr_df = generate_vogel_curve(q_max, p_r, num_points)

  q_array = ipr_df["Qo"].values
  hydrostatic = 0.33 * depth
  friction_factor = 0.0002

  pwf_vlp = p_wh + hydrostatic + friction_factor * (q_array**2)
  vlp_df = pd.DataFrame({"Pwf": pwf_vlp, "Qo": q_array})

  diff = np.abs(ipr_df["Pwf"].values - vlp_df["Pwf"].values)
  idx_oper = int(np.argmin(diff))

  q_oper = float(ipr_df["Qo"].values[idx_oper])
  pwf_oper = float(ipr_df["Pwf"].values[idx_oper])

  return {
      "ipr_df": ipr_df,
      "vlp_df": vlp_df,
      "q_oper": q_oper,
      "pwf_oper": pwf_oper,
  }


def explain_ipr_derivation(
    model_type: str,
    p_r: float,
    p_wf_test: float,
    q_test: float,
    p_b: float = None,
    n: float = None,
    c: float = None,
    j: float = None,
    q_max: float = None,
) -> str:
  """Generates step-by-step engineering markdown walking through governing equations,

  input substitutions, intermediate milestones, and deliverability envelope.
  """
  drawdown = p_r - p_wf_test
  j_val = j if j is not None else (q_test / max(drawdown, 1e-5))
  q_m = (
      q_max
      if q_max is not None
      else calculate_vogel_qmax(q_test, p_wf_test, p_r)
  )

  sections = [
      "### 📐 Step-by-Step Engineering Calculation & Derivation",
      f"**Selected Model:** {model_type}",
      f"- Reservoir Pressure ($P_R$): **{p_r:,.1f} psi**",
      f"- Test Flowing Pressure ($P_{{wf,\\text{{test}}}}$): **{p_wf_test:,.1f} psi**",
      f"- Test Flow Rate ($q_{{\\text{{test}}}}$): **{q_test:,.1f} STB/day**",
      f"- Pressure Drawdown ($\\Delta P = P_R - P_{{wf}}$): **{drawdown:,.1f} psi**",
      f"- Estimated Productivity Index ($J$): **{j_val:,.2f} STB/day/psi**",
  ]

  if "Vogel" in model_type and "Composite" not in model_type:
    ratio = p_wf_test / max(p_r, 1e-5)
    denom = 1.0 - 0.2 * ratio - 0.8 * (ratio**2)
    sections.extend([
        "#### Governing Equation: Vogel Inflow Performance Relationship (1968)",
        r"$$\frac{q_o}{q_{\max}} = 1 - 0.2\left(\frac{P_{wf}}{P_R}\right) - 0.8\left(\frac{P_{wf}}{P_R}\right)^2$$",
        f"- Pressure Ratio ($P_{{wf}}/P_R$): **{ratio:.4f}**",
        f"- Vogel Denominator ($1 - 0.2r - 0.8r^2$): **{denom:.4f}**",
        (
            "- Absolute Open Flow Potential ($AOFP / q_{\\max}$):"
            f" $\\mathbf{{{q_m:,.1f}\\text{{ STB/day}}}}$"
        ),
    ])

  elif "Composite" in model_type:
    pb = p_b if p_b is not None else 3000.0
    qb = j_val * max(p_r - pb, 0.0)
    sections.extend([
        "#### Governing Equations: Generalized Composite Inflow ($P_R > P_b$)",
        r"1. \textbf{Linear Darcy Flow above Bubble Point} ($P_{wf} \ge P_b$):",
        r"$$q_o = J(P_R - P_{wf})$$",
        r"2. \textbf{Vogel Two-Phase Flow below Bubble Point} ($P_{wf} < P_b$):",
        r"$$q_o = q_b + \frac{J \cdot P_b}{1.8}\left[1 - 0.2\left(\frac{P_{wf}}{P_b}\right) - 0.8\left(\frac{P_{wf}}{P_b}\right)^2\right]$$",
        f"- Bubble Point Pressure ($P_b$): {pb:,.1f} psi",
        f"- Oil Flow Rate at Bubble Point ($q_b$): {qb:,.1f} STB/day",
    ])

  elif "Fetkovich" in model_type:
    n_val = n if n is not None else 0.85
    pr2_pwf2 = max((p_r**2) - (p_wf_test**2), 1e-5)
    c_val = c if c is not None else (q_test / (pr2_pwf2**n_val))
    q_m = c_val * (p_r ** (2 * n_val))
    sections.extend([
        "#### Governing Equation: Fetkovich Empirical Backpressure Model",
        r"$$q_o = C(P_R^2 - P_{wf}^2)^n$$",
        f"- Flow Turbulence Exponent ($n$): {n_val:.2f}",
        f"- Deliverability Coefficient ($C$): {c_val:.6e} STB/day/psi^2n",
        f"- Maximum Potential Deliverability ($AOFP$): **{q_m:,.1f} STB/day**",
    ])

  else:
    sections.append(
        "Nodal system analysis integrating reservoir deliverability (Inflow) with"
        " vertical lift performance (Outflow) to compute operating flow point."
    )

  return "\n\n".join(sections)
