#!/usr/bin/env python3
"""
godding/serve.py
================

Tiny zero-dependency static server for local viewing. Why this exists:
opening index.html via file:// makes some browsers (notably Chrome) block
the JSON fetch() calls used by the home page and changelog. Run this script
and the site behaves the way it will once it's deployed.

    python serve.py            # binds 127.0.0.1:8000
    python serve.py 9000       # custom port
"""
from __future__ import annotations

import http.server
import os
import socketserver
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent

class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    os.chdir(ROOT)
    with socketserver.TCPServer(("127.0.0.1", port), NoCacheHandler) as srv:
        url = f"http://127.0.0.1:{port}/"
        print(f"godding · serving {ROOT} at {url}")
        print("ctrl-c to stop.")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print("\nbye.")

if __name__ == "__main__":
    main()
