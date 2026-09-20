import sqlite3
import json
import pandas as pd
from datetime import datetime

DB_NAME = "petrocalc.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initializes the local SQLite database with shift_logs and ipr_tests tables.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shift_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        well_name TEXT,
        thp REAL,
        chp REAL,
        choke REAL,
        liquid_rate REAL,
        water_cut REAL,
        raw_text TEXT,
        anomalies_json TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ipr_tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        well_name TEXT,
        model_type TEXT,
        p_r REAL,
        p_b REAL,
        p_wf_test REAL,
        q_test REAL,
        q_max REAL,
        j_index REAL
    )
    """)
    
    conn.commit()
    conn.close()

def save_shift_log(well_name: str, parsed_data: dict, anomalies: list):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    anomalies_json = json.dumps(anomalies)
    
    cursor.execute("""
    INSERT INTO shift_logs (timestamp, well_name, thp, chp, choke, liquid_rate, water_cut, raw_text, anomalies_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp,
        well_name,
        parsed_data.get("thp"),
        parsed_data.get("chp"),
        parsed_data.get("choke_size"),
        parsed_data.get("liquid_rate"),
        parsed_data.get("water_cut"),
        parsed_data.get("raw_text"),
        anomalies_json
    ))
    
    conn.commit()
    conn.close()

def get_shift_history() -> pd.DataFrame:
    init_db()
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM shift_logs ORDER BY id DESC", conn)
    conn.close()
    return df

def save_ipr_test(well_name: str, model_type: str, p_r: float, p_b: float, pwf_test: float, q_test: float, q_max: float, j_index: float):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
    INSERT INTO ipr_tests (timestamp, well_name, model_type, p_r, p_b, p_wf_test, q_test, q_max, j_index)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp, well_name, model_type, p_r, p_b, pwf_test, q_test, q_max, j_index
    ))
    
    conn.commit()
    conn.close()

def get_ipr_history() -> pd.DataFrame:
    init_db()
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM ipr_tests ORDER BY id DESC", conn)
    conn.close()
    return df
