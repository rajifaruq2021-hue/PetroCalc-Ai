import io
import re
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend safe for server threads
import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

# ---------------------------------------------------------
# Matplotlib Curve Rendering Helper
# ---------------------------------------------------------
def create_curve_chart_image(p_r, pwf_arr, qo_arr, p_wf_test=None, q_test=None, title="Deliverability Performance Envelope"):
    """
    Renders a publication-grade deliverability curve via matplotlib into an in-memory PNG buffer.
    """
    fig, ax = plt.subplots(figsize=(7.2, 4.0), dpi=220)
    
    # Plot curve
    ax.plot(qo_arr, pwf_arr, color="#0052cc", linewidth=2.4, label="Inflow Deliverability (IPR)")
    
    # Highlight operating test point if available
    if p_wf_test is not None and q_test is not None:
        ax.scatter([q_test], [p_wf_test], color="#d32f2f", s=70, zorder=5, 
                   label=f"Test Point ({q_test:,.0f} STB/d @ {p_wf_test:,.0f} psi)")
        ax.axvline(x=q_test, color="#d32f2f", linestyle=":", alpha=0.45)
        ax.axhline(y=p_wf_test, color="#d32f2f", linestyle=":", alpha=0.45)

    ax.set_title(title, fontsize=12, fontweight="bold", pad=12, color="#1e293b")
    ax.set_xlabel("Liquid Flow Rate, q_o (STB/day)", fontsize=10, fontweight="bold", color="#334155")
    ax.set_ylabel("Bottomhole Flowing Pressure, P_wf (psi)", fontsize=10, fontweight="bold", color="#334155")
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0, top=float(p_r) * 1.05 if p_r else None)
    
    ax.grid(True, linestyle="--", alpha=0.45, color="#cbd5e1")
    ax.legend(loc="upper right", frameon=True, facecolor="#f8fafc", edgecolor="#cbd5e1", fontsize=9)
    
    # Clean spines
    for spine in ax.spines.values():
        spine.set_color("#94a3b8")
        spine.set_linewidth(0.8)

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf

# ---------------------------------------------------------
# Markdown-to-ReportLab XML Sanitizer
# ---------------------------------------------------------
def clean_markdown_for_reportlab(text: str) -> list:
    """
    Converts raw markdown math/formatting into ReportLab-safe XML tags (<sub>, <sup>, <b>).
    Removes raw asterisks, backslashes, and latex delimiters.
    """
    lines = text.split("\n")
    cleaned_paragraphs = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Skip section divider artifacts
        if line.startswith("---") or line.startswith("==="):
            continue
            
        # Clean heading markers
        line = re.sub(r"^#{1,6}\s*", "", line)
        line = re.sub(r"^[■\*\-]\s*", "", line)
        
        # Clean LaTeX display delimiters
        line = line.replace("$$", "").replace("$", "")
        
        # Format bold tags
        line = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", line)
        
        # Common petroleum engineering sub/superscripts
        line = line.replace("P_R", "P<sub>R</sub>")
        line = line.replace("P_wf", "P<sub>wf</sub>")
        line = line.replace("P_b", "P<sub>b</sub>")
        line = line.replace("q_max", "q<sub>max</sub>")
        line = line.replace("q_test", "q<sub>test</sub>")
        line = line.replace("q_o", "q<sub>o</sub>")
        line = line.replace("q_b", "q<sub>b</sub>")
        line = line.replace("Delta P", "ΔP")
        line = line.replace("\\Delta P", "ΔP")
        line = line.replace("\\frac", "")
        line = line.replace("\\mathbf", "")
        line = line.replace("\\text", "")
        line = line.replace("\\ge", "≥")
        line = line.replace("\\le", "≤")
        line = line.replace("^2", "<sup>2</sup>")
        line = line.replace("^{2n}", "<sup>2n</sup>")
        line = line.replace("{", "").replace("}", "")
        line = line.replace("\\", "")

        cleaned_paragraphs.append(line)
        
    return cleaned_paragraphs

# ---------------------------------------------------------
# PDF Report Generator (ReportLab)
# ---------------------------------------------------------
def generate_pdf_report(well_name, model_type, inputs_dict, results_dict, derivation_text, curve_df):
    """
    Generates an executive, publication-grade PDF deliverability report with embedded chart.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        leftMargin=40, 
        rightMargin=40, 
        topMargin=36, 
        bottomMargin=36
    )
    styles = getSampleStyleSheet()
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocHeader',
        parent=styles['Heading1'],
        fontSize=17,
        leading=22,
        textColor=colors.HexColor('#0f2b5c'),
        fontName="Helvetica-Bold",
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubHeader',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#475569'),
        spaceAfter=14
    )
    sec_heading = ParagraphStyle(
        'SecHeading',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0f2b5c'),
        fontName="Helvetica-Bold",
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'ReportBody',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1e293b')
    )

    story = []
    
    # Header Banner
    story.append(Paragraph("PETROCALC AI — TECHNICAL DELIVERABILITY REPORT", title_style))
    story.append(Paragraph(f"<b>Well Identifier:</b> {well_name} &nbsp;|&nbsp; <b>Model Framework:</b> {model_type}", subtitle_style))
    story.append(Spacer(1, 4))
    
    # Section 1: Executive Parameters Table
    p_r = inputs_dict.get('p_r', 0.0)
    p_wf_test = inputs_dict.get('p_wf_test', 0.0)
    q_test = inputs_dict.get('q_test', 0.0)
    q_max = results_dict.get('q_max', 0.0)
    j_index = results_dict.get('j_index', 0.0)
    drawdown = max(p_r - p_wf_test, 0.0)

    table_data = [
        ["RESERVOIR & TEST INPUTS", "VALUE", "EVALUATED DELIVERABILITY METRICS", "VALUE"],
        ["Static Reservoir Pressure (P_R)", f"{p_r:,.1f} psi", "Absolute Open Flow Potential (AOFP)", f"{q_max:,.1f} STB/d"],
        ["Test Flowing Pressure (P_wf)", f"{p_wf_test:,.1f} psi", "Productivity Index (J)", f"{j_index:.3f} STB/d/psi"],
        ["Test Production Rate (q_test)", f"{q_test:,.1f} STB/d", "Net Pressure Drawdown (ΔP)", f"{drawdown:,.1f} psi"]
    ]
    
    summary_table = Table(table_data, colWidths=[150, 110, 160, 110])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f2b5c')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 10))

    # Section 2: Deliverability Curve Plot
    story.append(Paragraph("1. Inflow Deliverability Performance Curve", sec_heading))
    img_buf = create_curve_chart_image(
        p_r, 
        curve_df["Pwf"].values, 
        curve_df["Qo"].values, 
        p_wf_test, 
        q_test, 
        f"Deliverability Envelope: {well_name} ({model_type})"
    )
    story.append(RLImage(img_buf, width=480, height=260))
    story.append(Spacer(1, 8))

    # Section 3: Engineering Derivation
    story.append(Paragraph("2. Mathematical Formulation & Derivation Steps", sec_heading))
    formatted_paragraphs = clean_markdown_for_reportlab(derivation_text)
    for p_line in formatted_paragraphs:
        story.append(Paragraph(p_line, body_style))
        story.append(Spacer(1, 3))

    story.append(Spacer(1, 8))

    # Section 4: Sample Operating Points Table
    story.append(Paragraph("3. Calibrated Operating Coordinates (P_wf vs. q_o)", sec_heading))
    sample_indices = [0, len(curve_df)//4, len(curve_df)//2, (3*len(curve_df))//4, len(curve_df)-1]
    sample_data = [["Operating Stage", "Flowing Bottom-Hole Pressure (P_wf, psi)", "Oil Flow Rate (q_o, STB/day)"]]
    
    stages = ["Shut-In (P_R)", "High Pressure", "Mid Drawdown", "Deep Drawdown", "AOFP (P_wf = 0)"]
    for label, idx in zip(stages, sample_indices):
        pwf_val = curve_df["Pwf"].iloc[idx]
        qo_val = curve_df["Qo"].iloc[idx]
        sample_data.append([label, f"{pwf_val:,.1f}", f"{qo_val:,.1f}"])
        
    coord_table = Table(sample_data, colWidths=[160, 185, 185])
    coord_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#334155')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(coord_table)

    doc.build(story)
    buffer.seek(0)
    return buffer

# ---------------------------------------------------------
# Word Document Generator (.docx)
# ---------------------------------------------------------
def generate_word_report(well_name, model_type, inputs_dict, results_dict, derivation_text, curve_df):
    """
    Generates an executive, professionally styled Word technical document with embedded chart.
    """
    doc = Document()
    
    # Title & Subheading
    title_p = doc.add_paragraph()
    run_title = title_p.add_run("PetroCalc AI — Deliverability Engineering Memorandum")
    run_title.font.size = Pt(18)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(15, 43, 92)
    
    meta_p = doc.add_paragraph(f"Well Identifier: {well_name}  |  Model: {model_type}")
    meta_p.runs[0].font.size = Pt(10)
    meta_p.runs[0].font.color.rgb = RGBColor(71, 85, 105)

    # Key Parameters Table
    p_r = inputs_dict.get('p_r', 0.0)
    p_wf_test = inputs_dict.get('p_wf_test', 0.0)
    q_test = inputs_dict.get('q_test', 0.0)
    q_max = results_dict.get('q_max', 0.0)
    j_index = results_dict.get('j_index', 0.0)
    drawdown = max(p_r - p_wf_test, 0.0)

    table = doc.add_table(rows=1, cols=4)
    table.style = 'Light Shading Accent 1'
    hdr = table.rows[0].cells
    hdr[0].text, hdr[1].text, hdr[2].text, hdr[3].text = "Input Parameter", "Value", "Deliverability Metric", "Evaluated Value"
    
    data_rows = [
        ("Static Reservoir Pressure (P_R)", f"{p_r:,.1f} psi", "AOFP / Max Rate (q_max)", f"{q_max:,.1f} STB/d"),
        ("Test Flowing Pressure (P_wf)", f"{p_wf_test:,.1f} psi", "Productivity Index (J)", f"{j_index:.3f} STB/d/psi"),
        ("Test Production Rate (q_test)", f"{q_test:,.1f} STB/d", "Net Drawdown (ΔP)", f"{drawdown:,.1f} psi")
    ]
    for r in data_rows:
        row = table.add_row().cells
        row[0].text, row[1].text, row[2].text, row[3].text = r

    doc.add_paragraph()
    
    # Inflow Curve Section & Embedded Image
    h1 = doc.add_heading("1. Inflow Deliverability Performance Curve", level=2)
    img_buf = create_curve_chart_image(
        p_r, 
        curve_df["Pwf"].values, 
        curve_df["Qo"].values, 
        p_wf_test, 
        q_test, 
        f"Deliverability Envelope: {well_name}"
    )
    doc.add_picture(img_buf, width=Inches(6.2))
    caption = doc.add_paragraph("Figure 1: Generated deliverability inflow curve with operating test point.")
    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption.runs[0].font.size = Pt(8.5)
    caption.runs[0].font.italic = True

    # Derivation Section
    doc.add_heading("2. Mathematical Derivation & Solution Walkthrough", level=2)
    lines = derivation_text.split("\n")
    for line in lines:
        cleaned_line = line.strip().replace("$$", "").replace("$", "")
        cleaned_line = re.sub(r"^#{1,6}\s*", "", cleaned_line)
        cleaned_line = cleaned_line.replace("**", "")
        if cleaned_line:
            p = doc.add_paragraph(cleaned_line)
            p.paragraph_format.space_after = Pt(2)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

# ---------------------------------------------------------
# Excel Workbook Generator (.xlsx)
# ---------------------------------------------------------
def generate_excel_workbook(inputs_dict, results_dict, curve_df):
    """
    Outputs a formatted multi-sheet Excel workbook with metadata and coordinates.
    """
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Sheet 1: Summary KPIs
        summary_rows = [
            {"Parameter": "Static Reservoir Pressure (P_R, psi)", "Value": inputs_dict.get('p_r', 0.0)},
            {"Parameter": "Test Flowing Pressure (P_wf, psi)", "Value": inputs_dict.get('p_wf_test', 0.0)},
            {"Parameter": "Test Flow Rate (q_test, STB/d)", "Value": inputs_dict.get('q_test', 0.0)},
            {"Parameter": "Evaluated AOFP (q_max, STB/d)", "Value": results_dict.get('q_max', 0.0)},
            {"Parameter": "Productivity Index J (STB/d/psi)", "Value": results_dict.get('j_index', 0.0)},
        ]
        pd.DataFrame(summary_rows).to_excel(writer, sheet_name="Summary_KPIs", index=False)
        
        # Sheet 2: Curve Coordinates
        curve_df.to_excel(writer, sheet_name="Deliverability_Coordinates", index=False)
        
    buffer.seek(0)
    return buffer