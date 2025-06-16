#!/usr/bin/env python3
"""
Simple HTTP server for viewing HTMX components
"""

import http.server
import socketserver
import os

PORT = 8668
DIRECTORY = "static/components"

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

print(f"🚀 Starting HTMX Component Library Server on port {PORT}")
print(f"📁 Serving from: {os.path.abspath(DIRECTORY)}")
print(f"🌐 View at: http://localhost:{PORT}/")
print("Press Ctrl+C to stop")

with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    httpd.serve_forever()