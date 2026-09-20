def detect_anomalies(parsed_data: dict) -> list[dict]:
    """
    Applies physics heuristics and statistical rulebooks to evaluate parsed shift data
    and flag operational anomalies, safety risks, and well performance issues.
    """
    anomalies = []
    
    thp = parsed_data.get("thp")
    chp = parsed_data.get("chp")
    water_cut = parsed_data.get("water_cut")
    liquid_rate = parsed_data.get("liquid_rate")
    choke_size = parsed_data.get("choke_size")
    keywords = parsed_data.get("keywords", [])

    # Rule 1: High Casing Pressure relative to Tubing Head Pressure (Tubing-Casing Communication / Packer Leak)
    if thp is not None and chp is not None:
        if chp >= thp:
            anomalies.append({
                "severity": "Critical",
                "title": "Tubing-Casing Communication / Packer Leak",
                "description": f"Casing Head Pressure ({chp} psi) exceeds or equals Tubing Head Pressure ({thp} psi). Immediate packer and well integrity check required."
            })
        elif (chp / thp) > 0.85:
            anomalies.append({
                "severity": "Warning",
                "title": "High Casing Pressure Ratio",
                "description": f"Casing pressure ({chp} psi) is unusually close to tubing pressure ({chp/thp*100:.1f}% of THP). Monitor for annular gas migration."
            })

    # Rule 2: Water Cut and Liquid Loading symptoms
    if water_cut is not None:
        if water_cut > 70.0:
            anomalies.append({
                "severity": "Warning",
                "title": "High Water Cut Threshold Exceeded",
                "description": f"Water cut is at {water_cut}%. Accelerated reservoir depletion and potential artificial lift / plunger lift requirement."
            })

    # Rule 3: Sand or Flowline restriction keywords
    if "sand" in keywords:
        anomalies.append({
                "severity": "Critical",
                "title": "Sand Production Detected",
                "description": "Shift report mentions sand production. Risk of sand bridging, downhole pump erosion, and surface choke cutting."
        })

    if "slugging" in keywords:
        anomalies.append({
                "severity": "Informational",
                "title": "Intermittent Liquid Slugging",
                "description": "Operational notes indicate flow instability or slugging. Check separator level control and flowline pressure fluctuations."
        })

    if "wax" in keywords or "hydrate" in keywords:
        anomalies.append({
                "severity": "Warning",
                "title": "Flow Assurance Risk (Wax/Hydrates)",
                "description": "Report mentions paraffin/wax or hydrate formation tendency. Consider chemical batch treatment or thermal remediation."
        })

    # Rule 4: General low production combined with high choke
    if choke_size is not None and choke_size >= 32 and liquid_rate is not None and liquid_rate < 400:
        anomalies.append({
            "severity": "Warning",
            "title": "Suboptimal Productivity / Flow Restriction",
            "description": f"Large choke setting ({choke_size}/64\") yielding relatively low liquid rate ({liquid_rate} bopd). Possible downhole scale, paraffin deposition, or reservoir skin."
        })

    return anomalies
