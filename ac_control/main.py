# AC Control Main Application

# import annotations for Python 3.7+ to allow postponed
# evaluation of type hints
from __future__ import annotations

# Import necessary standard libraries
import argparse
import sys
import threading

from ac_control.automation import ACController, LoginConfig
from ac_control.scheduler import ScheduleRunner, Timetable
from ac_control.server import start_control_server
from ac_control.state import StatusStore

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

# Helper: IP getter
def get_local_ip() -> str:
    import socket
    try:
        # Connect to an external host to determine the local IP address
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
    except Exception:
        local_ip = "127.0.0.1"
    # Revoke import
    del socket
    # Return the local IP address
    return local_ip

# Main function
def main(argv: list[str] | None = None) -> None:

    # Print welcome message
    print("Welcome to the AC Control System!")

    # Parse command-line arguments
    args = parse_args(argv or sys.argv[1:])

    # Create login configuration
    login_config = LoginConfig(
        username = args.username,
        password = args.password,
        headless = args.headless
    )

    # Get the AC controller up and running
    print("Starting AC controller...")
    controller = ACController(login_config)
    controller.start()

    # Initialize status store, timetable, and scheduler
    status_store = StatusStore()
    timetable = Timetable()
    scheduler = ScheduleRunner(controller, timetable, status_store)
    scheduler.start()

    # Start the control server in a separate thread
    print(f"Starting control server on port {args.port}...")
    server = start_control_server(args.port, status_store, timetable, controller)
    server_thread = threading.Thread(target = server.serve_forever, daemon = True)
    server_thread.start()

    # Get the current machine's IP address
    local_ip = get_local_ip()

    # Keep the main thread alive while the server is runnings
    print(f"\n\033[1mWeb dashboard ready.\033[0m Please access it at:\n\thttp://localhost:{args.port} OR\n\thttp://{local_ip}:{args.port}\nfrom other devices on the same network.")
    print("Press \033[1m[Any Key]\033[0m to stop the application safely.")
    
    # Wait for user input to exit, or handle keyboard interrupt gracefully
    try:
        # Wait for user input to exit
        input() 
    except EOFError:
        pass 
   
    # Clean up resources on exit
    print("Stopping scheduler and server...")
    scheduler.stop()
    scheduler.join(timeout = 5)
    server.shutdown()
    print("Logging out from AC controller...")
    controller.logout()
    print("Application stopped.")

# Entry point
if __name__ == "__main__":
    main()