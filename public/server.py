#!/usr/bin/env python3
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json

class ChatHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/chat':
            length = int(self.headers['Content-Length'])
            body = self.rfile.read(length)
            data = json.loads(body)
            
            # Echo back for now - can be connected to OpenClaw later
            reply = f"收到: {data.get('message', '')}"
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'reply': reply}).encode())
        else:
            self.send_error(404)
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

HTTPServer(('0.0.0.0', 8080), ChatHandler).serve_forever()
