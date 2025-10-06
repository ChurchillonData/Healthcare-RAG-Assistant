#!/usr/bin/env python3
"""
Simple HTTP server to serve the frontend files
This avoids CORS issues when testing locally
"""

import http.server
import socketserver
import webbrowser
import os
from pathlib import Path

# Set the directory to serve
FRONTEND_DIR = Path(__file__).parent

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def serve_frontend(port=8080):
    """Start the frontend server"""
    os.chdir(FRONTEND_DIR)
    
    with socketserver.TCPServer(("", port), CustomHTTPRequestHandler) as httpd:
        print(f"🚀 Frontend server running at http://localhost:{port}")
        print(f"📁 Serving files from: {FRONTEND_DIR}")
        print(f"🌐 Opening browser...")
        
        # Open browser automatically
        webbrowser.open(f'http://localhost:{port}')
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped.")

if __name__ == "__main__":
    serve_frontend()
