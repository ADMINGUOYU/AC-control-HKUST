#!/usr/bin/env bash

# ---------- Configuration Section ----------
# Account credentials for AC Control server.
# NOTE: You can set these here or export them before hand.
if [[ -z "${AC_USERNAME:-}" || -z "${AC_PASSWORD:-}" ]]; then
  # If not set, use export them using the hardcoded values here
  export AC_USERNAME="<USERNAME>"
  export AC_PASSWORD="<PASSWORD>"
fi
# Optional: Set to "1" or "true" to run in headless mode (no GUI).
AC_HEADLESS="1"
# Optional: Set the port for the server (default is 8000).
AC_PORT="8000"
# -------------------------------------------

# This script starts the AC Control server.
# It checks for the virtual environment, 
# ensures that the necessary environment variables are set,
#  and then runs the main application with the appropriate 
# flags based on the configuration.

# Set strict mode for better error handling
set -euo pipefail

# Get the directory of the script to determine the project root
PROJECT_ROOT="$(cd -- "$(dirname "$0")" && pwd)"
VENV_PATH="${PROJECT_ROOT}/.venv"

# Environment checking
if [[ ! -d "${VENV_PATH}" ]]; then
  echo "Virtual environment not found. Run ${PROJECT_ROOT}/setup.sh first."
  exit 1
fi

# Adds the --headless flag if AC_HEADLESS is set to "1" or "true"
HEADLESS_FLAG=()
if [[ "${AC_HEADLESS:-}" == "1" || "${AC_HEADLESS:-}" == "true" ]]; then
  HEADLESS_FLAG+=(--headless)
fi

# Adds the --port flag
PORT_FLAG=("--port" "${AC_PORT}")

# [DEBUG] Print the configuration for verification
echo "Starting AC Control server with the following configuration:"
echo "  Username: ${AC_USERNAME}"
echo "  Password: ${AC_PASSWORD}"
echo "  Headless Mode: ${AC_HEADLESS}"
echo "  Port: ${AC_PORT}"

# Activate the virtual environment and run the main application
source "${VENV_PATH}/bin/activate"
python -m ac_control.main --username "${AC_USERNAME}" --password "${AC_PASSWORD}" "${PORT_FLAG[@]}" "${HEADLESS_FLAG[@]}"
