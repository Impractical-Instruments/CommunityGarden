#!/usr/bin/env python3
"""Simple HTTP server for FundingCAPTCHA. Serves files to any machine on the LAN."""
import http.server
import socketserver
import os
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
DIR = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)
    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} - {fmt % args}")

with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    import socket
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except Exception:
        local_ip = "127.0.0.1"
    print(f"FundingCAPTCHA server running:")
    print(f"  Local:   http://localhost:{PORT}/")
    print(f"  Network: http://{local_ip}:{PORT}/")
    print("Press Ctrl+C to stop.")
    httpd.serve_forever()
