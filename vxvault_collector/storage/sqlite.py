import sqlite3
import os

DB_PATH = os.path.join("data", "vxvault.db")

class SQLiteStore:
    def __init__(self):
        # Veri dizininin var olduğundan emin olalım
        os.makedirs("data", exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self.cur = self.conn.cursor()
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS iocs (
            date TEXT,
            url TEXT,
            md5 TEXT UNIQUE,
            ip TEXT,
            tools TEXT,
            details_id TEXT,
            sha1 TEXT,
            sha256 TEXT,
            size TEXT,
            filename TEXT,
            tools_links TEXT
        )
        """)
        self.conn.commit()

        # Eksik sütunları ekle (Şema güncelleme)
        for col in ["details_id", "sha1", "sha256", "size", "filename", "tools_links"]:
            try:
                self.cur.execute(f"ALTER TABLE iocs ADD COLUMN {col} TEXT")
            except sqlite3.OperationalError:
                pass # Sütun zaten var
        self.conn.commit()

    def insert_many(self, items):
        self.cur.executemany(
            "REPLACE INTO iocs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(i.date, i.url, i.md5, i.ip, i.tools, i.details_id, i.sha1, i.sha256, i.size, i.filename, i.tools_links) for i in items]
        )
        self.conn.commit()

    def get_all(self, limit=100):
        self.cur.execute("SELECT * FROM iocs ORDER BY date DESC LIMIT ?", (limit,))
        return self.cur.fetchall()

    def search(self, query):
        q = f"%{query}%"
        self.cur.execute("""
            SELECT * FROM iocs 
            WHERE md5 LIKE ? OR ip LIKE ? OR url LIKE ? OR sha1 LIKE ? OR sha256 LIKE ?
            ORDER BY date DESC
        """, (q, q, q, q, q))
        return self.cur.fetchall()
