# This module implements a simple HTTP server that serves
# the current status of the AC unit as JSON.
# Connect to http://ip:8000/status NOTE: Not https

from __future__ import annotations

# Import necessary modules
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable

from ac_control.state import StatusStore

# Define a request handler for the HTTP server that serves the
# AC status as JSON
class StatusRequestHandler(BaseHTTPRequestHandler):

    def __init__(self, status_provider: Callable[[], dict], *args, **kwargs):
        self._status_provider = status_provider
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.path not in ("/", "/status"):
            self.send_error(404, "Not Found")
            return
        payload = self._status_provider()
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Reduce console noise
        return

# Function to start the HTTP server on the specified port, 
# using the provided status store to serve the AC status.
def start_status_server(port: int, store: StatusStore) -> HTTPServer:
    def handler(*args, **kwargs):
        return StatusRequestHandler(
            lambda: store.get_snapshot().to_dict(), *args, **kwargs
        )

    server = HTTPServer(("0.0.0.0", port), handler)
    return server