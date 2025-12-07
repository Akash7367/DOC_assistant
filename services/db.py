# services/db.py
import sqlite3
import os
import json
from datetime import datetime
from typing import Optional, List, Dict

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'history.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT,
    context TEXT,
    risk_json TEXT,
    escalated INTEGER DEFAULT 0,
    source_count INTEGER DEFAULT 0,
    model_used TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript(CREATE_SQL)
    conn.commit()
    conn.close()

def save_interaction(question: str, answer: str, context: str = "", risk: dict = None,
                     escalated: bool = False, source_count: int = 0, model_used: Optional[str] = None) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO history (question, answer, context, risk_json, escalated, source_count, model_used, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (question, answer, context, json.dumps(risk or {}), 1 if escalated else 0, source_count, model_used or "", datetime.utcnow().isoformat())
    )
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id

def list_history(limit: int = 100) -> List[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    # parse risk_json
    for r in rows:
        try:
            r['risk'] = json.loads(r.get('risk_json') or "{}")
        except Exception:
            r['risk'] = {}
        r.pop('risk_json', None)
    return rows

def get_history_item(item_id: int) -> Optional[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM history WHERE id = ?", (item_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    r = dict(row)
    try:
        r['risk'] = json.loads(r.get('risk_json') or "{}")
    except Exception:
        r['risk'] = {}
    r.pop('risk_json', None)
    return r

def export_all_for_langsmith() -> List[Dict]:
    """
    Export all history as a list of dicts suitable for ingestion.
    LangSmith/other tools typically accept JSON lines or a JSON array. Return array here.
    Each record: {id, question, answer, context, risk, escalated, source_count, model_used, created_at}
    """
    rows = list_history(limit=10000)
    # ensure consistent fields
    for r in rows:
        r['escalated'] = bool(r.get('escalated'))
        r['source_count'] = int(r.get('source_count') or 0)
    return rows
