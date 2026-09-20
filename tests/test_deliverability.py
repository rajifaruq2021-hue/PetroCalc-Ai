import unittest
import pandas as pd
import numpy as np
import io

from calculations.ipr import (
    calculate_vogel_qmax,
    generate_vogel_curve,
    generate_composite_curve,
    generate_fetkovich_curve,
    calculate_productivity_index
)
from parser.log_parser import parse_shift_note
from diagnostics.anomaly_engine import detect_anomalies
from utils.document_io import generate_word_report, generate_pdf_report

class TestPetroCalcAI(unittest.TestCase):

    def test_vogel_calculations(self):
        q_test, pwf_test, pr = 1200.0, 2000.0, 3500.0
        q_max = calculate_vogel_qmax(q_test, pwf_test, pr)
        self.assertGreater(q_max, q_test)
        
        df = generate_vogel_curve(q_max, pr, num_points=50)
        self.assertEqual(len(df), 50)
        # Check monotonicity: Pwf decreases while Qo increases
        self.assertGreater(df["Pwf"].iloc[0], df["Pwf"].iloc[-1])
        self.assertLess(df["Qo"].iloc[0], df["Qo"].iloc[-1])

    def test_composite_curve(self):
        pr, pb, j = 4000.0, 3000.0, 1.5
        df = generate_composite_curve(pr, pb, j_index=j, num_points=50)
        self.assertEqual(len(df), 50)
        self.assertFalse(df.empty)

    def test_fetkovich_curve(self):
        pr, q_test, pwf_test = 3500.0, 1200.0, 2000.0
        df = generate_fetkovich_curve(pr, q_test, pwf_test, n=0.85, num_points=50)
        self.assertEqual(len(df), 50)
        self.assertGreater(df["Qo"].iloc[-1], 0.0)

    def test_parser_and_anomalies(self):
        sample_text = (
            "Well-02 report: Choke 36/64, THP down to 780 psi, CHP noted at 800 psi. "
            "Liquid rate 380 bopd with BS&W water cut spiking to 72%. Minor sand production observed."
        )
        parsed = parse_shift_note(sample_text)
        self.assertEqual(parsed["thp"], 780.0)
        self.assertEqual(parsed["chp"], 800.0)
        self.assertEqual(parsed["water_cut"], 72.0)
        self.assertIn("sand", parsed["keywords"])

        anomalies = detect_anomalies(parsed)
        critical_titles = [a["title"] for a in anomalies if a["severity"] == "Critical"]
        self.assertIn("Tubing-Casing Communication / Packer Leak", critical_titles)
        self.assertIn("Sand Production Detected", critical_titles)

    def test_document_reports(self):
        inputs = {"Reservoir Pressure (psi)": 3500.0, "Test Pwf (psi)": 2000.0}
        results = {"Max Oil Rate / AOFP": "2,400.0 STB/d"}
        derivation = "Step 1: Vogel equation derivation..."
        curve_df = generate_vogel_curve(2400.0, 3500.0, num_points=20)

        word_io = generate_word_report("Well-01", "Tier 1: Vogel", inputs, results, derivation, curve_df)
        self.assertIsInstance(word_io, io.BytesIO)
        self.assertGreater(word_io.getbuffer().nbytes, 0)

        pdf_io = generate_pdf_report("Well-01", "Tier 1: Vogel", inputs, results, derivation, curve_df)
        self.assertIsInstance(pdf_io, io.BytesIO)
        self.assertGreater(pdf_io.getbuffer().nbytes, 0)

if __name__ == "__main__":
    unittest.main()
