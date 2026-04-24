#!/usr/bin/env python3
"""
FundingCAPTCHA server.
Serves static files + handles photo uploads + pairs config API.
Binds to 0.0.0.0 so any machine on the LAN can reach it.

Endpoints:
  POST /upload          JSON {label, name, data:"data:image/...;base64,..."}
  GET  /api/photos      JSON list of uploaded photos
  GET  /api/pairs       JSON pairs config
  POST /api/pairs       Save pairs config
  GET  /*               Static file serving
"""
import http.server
import socketserver
import os
import sys
import json
import base64
import uuid
from pathlib import Path

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
DIR = Path(os.path.dirname(os.path.abspath(__file__)))
UPLOADS_DIR = DIR / 'uploads'
UPLOADS_DIR.mkdir(exist_ok=True)
PAIRS_FILE = DIR / 'pairs.json'
MAX_UPLOAD_BYTES = 12 * 1024 * 1024  # 12 MB base64-encoded ceiling


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIR), **kwargs)

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------
    def do_GET(self):
        if self.path == '/api/photos':
            self._get_photos()
        elif self.path == '/api/pairs':
            self._get_pairs()
        else:
            super().do_GET()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        if length > MAX_UPLOAD_BYTES:
            self._json(400, {'ok': False, 'error': 'Upload too large'})
            return
        body = self.rfile.read(length)

        if self.path == '/upload':
            self._post_upload(body)
        elif self.path == '/api/pairs':
            self._post_pairs(body)
        else:
            self.send_error(404)

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------
    def _post_upload(self, body):
        try:
            data   = json.loads(body)
            label  = str(data.get('label', 'untitled')).strip()[:80] or 'untitled'
            who    = str(data.get('name', '')).strip()[:40]
            imgstr = data.get('data', '')

            if ',' not in imgstr:
                raise ValueError('Missing data URL comma separator')
            header, b64 = imgstr.split(',', 1)

            ext = 'jpg'
            if 'png'  in header: ext = 'png'
            elif 'gif' in header: ext = 'gif'
            elif 'webp' in header: ext = 'webp'

            safe_label = label.replace(' ', '_').replace('/', '_')
            safe_who   = who.replace(' ', '_').replace('/', '_')
            prefix     = f"{safe_who}__" if safe_who else ''
            filename   = f"{uuid.uuid4().hex[:8]}__{prefix}{safe_label}.{ext}"
            filepath   = UPLOADS_DIR / filename

            with open(filepath, 'wb') as f:
                f.write(base64.b64decode(b64))

            print(f"  UPLOAD  {filename}  ({len(b64)//1024} kB b64)")
            self._json(200, {'ok': True, 'filename': filename, 'url': f'/uploads/{filename}'})
        except Exception as e:
            self._json(400, {'ok': False, 'error': str(e)})

    def _get_photos(self):
        photos = []
        for f in sorted(UPLOADS_DIR.iterdir()):
            if f.suffix.lower() not in ('.jpg', '.jpeg', '.png', '.gif', '.webp'):
                continue
            # filename pattern: <hex>__<who>__<label>.<ext>  or  <hex>__<label>.<ext>
            stem  = f.stem
            parts = stem.split('__', 2)
            if len(parts) == 3:
                _, who, label = parts
            elif len(parts) == 2:
                _, label = parts
                who = ''
            else:
                label = stem
                who = ''
            photos.append({
                'filename': f.name,
                'url':      f'/uploads/{f.name}',
                'label':    label.replace('_', ' '),
                'who':      who.replace('_', ' '),
            })
        self._json(200, photos)

    def _get_pairs(self):
        if PAIRS_FILE.exists():
            with open(PAIRS_FILE) as fh:
                self._json(200, json.load(fh))
        else:
            self._json(200, [])

    def _post_pairs(self, body):
        try:
            pairs = json.loads(body)
            with open(PAIRS_FILE, 'w') as fh:
                json.dump(pairs, fh, indent=2)
            print(f"  PAIRS   saved {len(pairs)} pair(s)")
            self._json(200, {'ok': True, 'count': len(pairs)})
        except Exception as e:
            self._json(400, {'ok': False, 'error': str(e)})

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} - {fmt % args}")


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------
with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    import socket
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except Exception:
        local_ip = "127.0.0.1"

    print(f"FundingCAPTCHA server running on port {PORT}")
    print(f"  Games:    http://{local_ip}:{PORT}/")
    print(f"  Upload:   http://{local_ip}:{PORT}/upload.html   ← share with kids")
    print(f"  Gallery:  http://{local_ip}:{PORT}/gallery.html  ← your pairing tool")
    print("Press Ctrl+C to stop.\n")
    httpd.serve_forever()
