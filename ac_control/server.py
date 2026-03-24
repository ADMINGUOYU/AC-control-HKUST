# This module implements a simple HTTP server that serves
# the current status of the AC unit as JSON.

from __future__ import annotations

# Import necessary modules
import json
from pathlib import Path
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable

from ac_control.automation import ACController
from ac_control.scheduler import Timetable
from ac_control.state import StatusStore

# Load the dashboard HTML content at startup
# this file path ../html/dashboard.html
DASHBOARD_PATH = Path(__file__).parent.parent / "html" / "dashboard.html"
if not DASHBOARD_PATH.is_file():
    print(f"Warning: Dashboard HTML file not found at {DASHBOARD_PATH}. The dashboard will not be available.")
try:
    INDEX_HTML = DASHBOARD_PATH.read_bytes()
except FileNotFoundError:
    INDEX_HTML = b"<html><body>Dashboard missing</body></html>"

# Define the request handler for the control server
class ControlRequestHandler(BaseHTTPRequestHandler):
    def __init__(
        self,
        *args,
        status_provider: Callable[[], dict],
        timetable: Timetable,
        controller: ACController,
        **kwargs,
    ):
        self._status_provider: Callable[[], dict] = status_provider
        self._timetable: Timetable = timetable
        self._controller: ACController = controller
        super().__init__(*args, **kwargs)

    # Handle GET requests for the dashboard and API endpoints
    def do_GET(self):
        if self.path == "/":
            self._send_response(HTTPStatus.OK, INDEX_HTML, content_type = "text/html")
            return
        if self.path == "/api/status":
            payload = self._status_provider()
            self._send_json(HTTPStatus.OK, payload)
            return
        if self.path == "/api/schedules":
            self._send_json(HTTPStatus.OK, {"schedules": self._timetable.list_schedule_dicts()})
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    # Handle POST requests for toggling power and adding schedules
    def do_POST(self):
        if self.path == "/api/toggle":
            success = self._controller.toggle_power()
            if success:
                self._send_json(HTTPStatus.OK, {"success": True})
            else:
                self._send_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"success": False, "error": "Toggle operation failed; please try again shortly."},
                )
            return

        if self.path == "/api/schedules":
            try:
                payload = self._read_json()
                schedule = self._timetable.add_schedule(
                    payload.get("start_time", ""),
                    payload.get("end_time", ""),
                    int(payload.get("on_duration", 0)),
                    int(payload.get("off_duration", 0)),
                    payload.get("name"),
                )
            except (ValueError, TypeError) as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return

            self._send_json(HTTPStatus.CREATED, schedule.to_dict())
            return
        
        if self.path == "/api/enable_schedules":
            # TODO: to implement
            print("POST received ... to be implemented")
            self._send_json(HTTPStatus.OK, {"success": True})
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    # Handle DELETE requests for removing schedules
    def do_DELETE(self):
        if self.path.startswith("/api/schedules/"):
            schedule_id = self.path.split("/")[-1]
            removed = self._timetable.remove_schedule(schedule_id)
            if removed:
                self._send_response(HTTPStatus.NO_CONTENT, b"", content_type = "application/json")
            else:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Schedule not found"})
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    # Helper methods for reading JSON
    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b"{}"
        return json.loads(body)

    # Helper methods for sending responses
    def _send_json(self, status_code: HTTPStatus, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self._send_response(status_code, body, content_type = "application/json")

    # General method for sending HTTP responses
    def _send_response(self, status_code: HTTPStatus, body: bytes, content_type: str) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    # Override log_message to suppress default logging to stderr
    def log_message(self, format, *args):
        return

# Function to start the control server
def start_control_server(port: int, status_store: StatusStore, timetable: Timetable, controller: ACController) -> HTTPServer:
    
    # Define a custom handler factory to inject dependencies
    # into the request handler
    def handler(*args, **kwargs):
        return ControlRequestHandler(
            *args,
            status_provider = lambda: status_store.get_snapshot().to_dict(),
            timetable = timetable,
            controller = controller,
            **kwargs,
        )
    # Create and return the HTTP server instance
    server = HTTPServer(("0.0.0.0", port), handler)
    return server