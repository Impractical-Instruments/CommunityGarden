#!/usr/bin/env python3
"""Serve the show dashboard as a static HTTP site.

Usage:
  python serve.py           # default port 9000
  python serve.py 9001      # custom port
"""

import http.server
import os
import socket
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9000
os.chdir(os.path.dirname(os.path.abspath(__file__)))

try:
    local_ip = socket.gethostbyname(socket.gethostname())
except Exception:
    local_ip = "127.0.0.1"

print(f"Show Dashboard:  http://{local_ip}:{PORT}/")
print("Press Ctrl+C to stop.\n")


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


with http.server.HTTPServer(("0.0.0.0", PORT), _QuietHandler) as httpd:
    httpd.serve_forever()
