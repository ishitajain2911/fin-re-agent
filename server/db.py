
import sqlite3
from typing import Optional
from server.schemas import SynthesisReport

DB_PATH = "data/reports.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            query TEXT NOT NULL,
            report_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_report(ticker: str, query: str, report: SynthesisReport):
    conn = get_connection()
    conn.execute(
        "INSERT INTO reports (ticker, query, report_json) VALUES (?, ?, ?)",
        (ticker, query, report.model_dump_json()),          # blank 1: which 3 values? (one needs converting to a JSON string)
    )
    conn.commit()                                 # blank 2: what makes the write stick?
    conn.close()


def get_cached_report(ticker: str, query: str) -> Optional[SynthesisReport]:
    conn = get_connection()
    row = conn.execute(
        """SELECT report_json FROM reports
           WHERE ticker = ? AND query = ?
             AND created_at >= datetime('now', '-1 day')
           ORDER BY created_at DESC
           LIMIT 1""",
        (ticker, query),
    ).fetchone()                           # gives a tuple like ('ne if no match
    conn.close()

    if row is None:                             # blank 3: what if nothing was found?
        return None
    return SynthesisReport.model_validate_json(row[0])

def list_reports(limit: int = 10) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT ticker, query, report_json, created_at FROM reports
           ORDER BY created_at DESC
           LIMIT ?""",
        (limit,),                          # the comma matters! (limit) is just a number; (limit,) is a 1-item tuple
    ).fetchall()                             # blank 1: fetchone gave ONE row. What gives ALL of them?
    conn.close()

    reports = []
    for ticker, query, report_json, created_at in rows:     # each row is a 4-item tuple, unpacked like (prev, k) in LC 394
        reports.append({
            "ticker": ticker,
            "query": query,
            "created_at": created_at,
            "report": SynthesisReport.model_validate_json(report_json),              # blank 2: turn report_json back into a SynthesisReport
        })
    return reports
