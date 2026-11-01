"""Durable alert outbox (SQLite). An alert is marked sent only after the backend echoes its UUID."""
import json
import sqlite3
import threading
import uuid


class Outbox:
    def __init__(self, path):
        self.lock = threading.RLock()
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('CREATE TABLE IF NOT EXISTS alerts(id TEXT PRIMARY KEY, payload TEXT, sent INTEGER DEFAULT 0)')
        self.db.commit()

    def add(self, payload):
        p = dict(payload, alert_id=uuid.uuid4().hex)
        with self.lock:
            self.db.execute('INSERT INTO alerts(id, payload) VALUES(?, ?)', (p['alert_id'], json.dumps(p)))
            self.db.commit()
        return p['alert_id']

    def pending(self, limit=100):
        with self.lock:
            return self.db.execute('SELECT id, payload FROM alerts WHERE sent=0 ORDER BY rowid LIMIT ?', (limit,)).fetchall()

    def ack(self, alert_id):
        with self.lock:
            self.db.execute('UPDATE alerts SET sent=1 WHERE id=?', (alert_id,))
            self.db.commit()

    def counts(self):
        with self.lock:
            rows = dict(self.db.execute('SELECT sent, COUNT(*) FROM alerts GROUP BY sent').fetchall())
        return {'pending': rows.get(0, 0), 'sent': rows.get(1, 0)}
