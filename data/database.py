import sqlite3
import json
import pandas as pd
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_path="data/website_analysis.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS crawl_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            website_url TEXT,
            crawled_at TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            url TEXT,
            status_code INTEGER,
            title TEXT,
            meta_description TEXT,
            load_time_seconds REAL,
            word_count INTEGER,
            image_count INTEGER,
            internal_links_count INTEGER,
            h1_tags TEXT,
            h2_tags TEXT,
            crawled_at TEXT,
            FOREIGN KEY(session_id) REFERENCES crawl_sessions(id)
        )
        """)

        self.conn.commit()

    def save_crawl_data(self, website_url, pages_data):
        cursor = self.conn.cursor()

        crawled_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO crawl_sessions (website_url, crawled_at) VALUES (?, ?)",
            (website_url, crawled_at)
        )
        session_id = cursor.lastrowid

        for page in pages_data:
            cursor.execute("""
                INSERT INTO pages (
                    session_id, url, status_code, title, meta_description,
                    load_time_seconds, word_count, image_count,
                    internal_links_count, h1_tags, h2_tags, crawled_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                page.get("url"),
                page.get("status_code"),
                page.get("title"),
                page.get("meta_description"),
                page.get("load_time_seconds"),
                page.get("word_count"),
                page.get("image_count"),
                page.get("internal_links_count"),
                json.dumps(page.get("h1_tags", [])),
                json.dumps(page.get("h2_tags", [])),
                page.get("crawled_at")
            ))

        self.conn.commit()
        return session_id

    def get_summary(self, session_id):
        df = pd.read_sql_query(
            "SELECT * FROM pages WHERE session_id = ?",
            self.conn,
            params=(session_id,)
        )

        summary = {
            "Total Pages": len(df),
            "Average Load Time": round(df["load_time_seconds"].mean(), 3) if not df.empty else 0,
            "Total Images": int(df["image_count"].sum()) if not df.empty else 0,
            "Total Links": int(df["internal_links_count"].sum()) if not df.empty else 0,
            "Broken Pages": int((df["status_code"] != 200).sum()) if not df.empty else 0
        }

        return summary, df

    def close(self):
        self.conn.close()