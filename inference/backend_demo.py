"""Operations-centre stand-in (LAB ONLY: no auth/TLS). Stores alerts once per UUID and echoes the UUID.
Run: python -m inference.backend_demo     then set BACKEND_URL=http://localhost:8080/alerts"""
import json
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            n = int(self.headers.get('Content-Length', '0'))
            if not 0 < n <= 65536:
                raise ValueError('bad length')
            alert = json.loads(self.rfile.read(n))
            with sqlite3.connect('backend_alerts.sqlite') as db:
                db.execute('CREATE TABLE IF NOT EXISTS alerts(id TEXT PRIMARY KEY, payload TEXT)')
                db.execute('INSERT OR IGNORE INTO alerts VALUES(?, ?)', (alert['alert_id'], json.dumps(alert)))
            body = json.dumps({'alert_id': alert['alert_id']}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(body)
        except (ValueError, KeyError):
            self.send_error(400)


if __name__ == '__main__':
    print('backend listening on http://127.0.0.1:8080/alerts')
    HTTPServer(('127.0.0.1', 8080), Handler).serve_forever()
