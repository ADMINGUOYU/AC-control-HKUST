# AC Control Main Application

# import annotations for Python 3.7+ to allow postponed
# evaluation of type hints
from __future__ import annotations

# Import necessary standard libraries
import argparse
import sys
import threading

from ac_control.automation import ACController, LoginConfig
from ac_control.server import start_status_server
from ac_control.state import StatusStore
from ac_control.ui import ACControlWindow

# Argument parser
def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description = "AC controller launcher")
    parser.add_argument(
        "-u",
        "--username",
        required = True,
        help = "Login username (will not be stored).",
    )
    parser.add_argument(
        "-p",
        "--password",
        required = True,
        help = "Login password (will not be stored).",
    )
    parser.add_argument(
        "--headless",
        action = "store_true",
        help = "Use Chrome headless mode (DUO 2FA typically fails in headless mode).",
    )
    parser.add_argument(
        "--port",
        type = int,
        default = 8000,
        help = "Port to expose status endpoint (accessible on 0.0.0.0).",
    )
    return parser.parse_args(argv)

# Main function
def main(argv: list[str] | None = None) -> None:

    # Parse command-line arguments
    args = parse_args(argv or sys.argv[1:])

    # Create login configuration
    login_config = LoginConfig(
        username = args.username, 
        password = args.password, 
        headless = args.headless
    )

    # Get the AC controller up and running
    controller = ACController(login_config)
    controller.start()
    
    # Initialize the status store and start the status server 
    # in a separate thread
    status_store = StatusStore()

    # Start the status server in a separate thread to avoid blocking
    # the main thread
    server = start_status_server(args.port, status_store)
    threading.Thread(target = server.serve_forever, daemon = True).start()

    # Start the UI (this will block until the UI is closed)
    # Hand over control
    ACControlWindow(controller, status_store)

# Entry point
if __name__ == "__main__":
    main()