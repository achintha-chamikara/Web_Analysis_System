import sqlite3
import json
import pandas as pd
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="data/website_analysis.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crawl_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                website_url TEXT NOT NULL,
                crawled_at TEXT NOT NULL,
                total_pages INTEGER,
                avg_load_time REAL,
                total_images INTEGER,
                total_links INTEGER
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                url TEXT,
                title TEXT,
                meta_description TEXT,
                status_code INTEGER,
                load_time_seconds REAL,
                word_count INTEGER,
                image_count INTEGER,
                internal_links_count INTEGER,
                h1_tags TEXT,
                h2_tags TEXT,
                crawled_at TEXT,
                FOREIGN KEY (session_id) REFERENCES crawl_sessions(id)
            )
        ''')

        self.conn.commit()
        print("  [DB] Tables ready ✓")

    def save_crawl_data(self, website_url, pages_data):
        cursor = self.conn.cursor()

        avg_load = round(sum(p["load_time_seconds"] for p in pages_data) / len(pages_data), 3)
        total_images = sum(p["image_count"] for p in pages_data)
        total_links = sum(p["internal_links_count"] for p in pages_data)

        cursor.execute('''
            INSERT INTO crawl_sessions (website_url, crawled_at, total_pages, avg_load_time, total_images, total_links)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (website_url, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              len(pages_data), avg_load, total_images, total_links))

        session_id = cursor.lastrowid

        for page in pages_data:
            cursor.execute('''
                INSERT INTO pages (session_id, url, title, meta_description, status_code,
                                   load_time_seconds, word_count, image_count,
                                   internal_links_count, h1_tags, h2_tags, crawled_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                page["url"],
                page["title"],
                page["meta_description"],
                page["status_code"],
                page["load_time_seconds"],
                page["word_count"],
                page["image_count"],
                page["internal_links_count"],
                json.dumps(page["h1_tags"]),
                json.dumps(page["h2_tags"]),
                page["crawled_at"]
            ))

        self.conn.commit()
        print(f"  [DB] Saved {len(pages_data)} pages under session ID {session_id} ✓")
        return session_id

    def get_summary(self, session_id):
        df_pages = pd.read_sql_query(
            "SELECT * FROM pages WHERE session_id = ?",
            self.conn, params=(session_id,)
        )

        summary = {
            "total_pages": len(df_pages),
            "avg_load_time": round(df_pages["load_time_seconds"].mean(), 3),
            "max_load_time": round(df_pages["load_time_seconds"].max(), 3),
            "min_load_time": round(df_pages["load_time_seconds"].min(), 3),
            "total_images": int(df_pages["image_count"].sum()),
            "total_links": int(df_pages["internal_links_count"].sum()),
            "avg_word_count": round(df_pages["word_count"].mean(), 1),
            "broken_pages": int((df_pages["status_code"] != 200).sum()),
            "slowest_page": df_pages.loc[df_pages["load_time_seconds"].idxmax(), "url"],
            "most_linked_page": df_pages.loc[df_pages["internal_links_count"].idxmax(), "url"],
        }

        return summary, df_pages

    def close(self):
        self.conn.close()