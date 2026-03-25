#!/usr/bin/env bash

# This script sets up a Python virtual environment for the project, 
# installs dependencies, and preinstalls chromedriver for Selenium tests. 

# Set strict mode for better error handling
set -euo pipefail

# Get the absolute path to the project root directory
PROJECT_ROOT="$(cd -- "$(dirname "$0")" && pwd)"
VENV_PATH="${PROJECT_ROOT}/.venv"

# First determine OS and architecture
OS_TYPE="$(uname -s)"
ARCH_TYPE="$(uname -m)"

# Check python cmd
if command -v python3 &> /dev/null; then
    PYTHON_EXE="python3"
else
    PYTHON_EXE="python"
fi

# Make source command work on Windows and Linux/MacOS
if [[ "${OS_TYPE}" == "MINGW"* || "${OS_TYPE}" == "CYGWIN"* || "${OS_TYPE}" == "MSYS"* ]]; then
    VENV_BIN="${VENV_PATH}/Scripts"
else
    VENV_BIN="${VENV_PATH}/bin"
fi

# Create virtual environment and install dependencies
${PYTHON_EXE} -m venv "${VENV_PATH}"
# Check if the virtual environment was created successfully
if [[ ! -f "${VENV_BIN}/activate" ]]; then
    echo "Error: Virtual environment activation script not found. Please check the setup script and try again."
    exit 1
fi
source "${VENV_BIN}/activate"
pip install --upgrade pip
pip install -r "${PROJECT_ROOT}/requirements.txt"

# Preinstall chromedriver inside the virtual environment
# ARM LINUX is not officially supported by Google,
# We have to use apt to download chromedriver for ARM-based Linux systems
if [[ "${OS_TYPE}" == "Linux" && "${ARCH_TYPE}" == "aarch64" ]]; then
    echo -e "\033[0;33mDetected Linux ARM architecture. Installing chromedriver via apt...\033[0m"
    # We download chromedriver ONLY, no sudo needed
    # Check if apt is available
    if ! command -v apt &> /dev/null; then
        echo "Error: apt package manager not found. Please install chromedriver manually for ARM-based Linux."
        exit 1
    fi
    # Get Chromium version to match chromedriver version
    if ! command -v chromium-browser &> /dev/null && ! command -v chromium &> /dev/null; then
        echo "Error: Chromium browser not found. Please install Chromium to get the correct chromedriver version."
        exit 1
    fi
    CHROME_VERSION=$(chromium-browser --version 2>/dev/null || chromium --version 2>/dev/null | awk '{print $2}')
    echo "Detected Chrome/Chromium version: ${CHROME_VERSION}. Installing matching chromedriver..."
    # Try to download, if no matched version found, we try to find if
    # we already have the driver installed, if not, we will fail and
    # ask user to install chromedriver manually (no root needed)
    if ! apt download "chromium-driver=$(echo "${CHROME_VERSION}" | cut -d. -f1-3)*" &> /dev/null; then
        echo -e "\033[0;33mWarning: No matching chromedriver version found in apt repositories.\033[0m"
        # Check if chromedriver is already installed in the system
        if command -v chromedriver &> /dev/null; then
            echo -e "\033[0;33mFound existing chromedriver in the system. Using it for the virtual environment.\033[0m"
            # Copy the existing chromedriver to the virtual environment
            cp "$(which chromedriver)" "${VENV_BIN}/chromedriver"
        else
            echo -e "\033[0;31mError: No matching chromedriver version found in apt repositories and no existing chromedriver found in the system. Please install chromedriver manually for ARM-based Linux.\033[0m"
            echo "NOTE: After installing chromedriver, please delete the .venv directory and run this setup script again."
            exit 1
        fi
    else
        # Extract the downloaded .deb file to get chromedriver binary
        DEB_FILE=$(ls chromium-driver_*.deb | head -n 1)
        echo "Extracting chromedriver from ${DEB_FILE}..."
        dpkg-deb --fsys-tarfile "${DEB_FILE}" | tar -xOf - ./usr/bin/chromedriver > "${VENV_BIN}/chromedriver"
        # Clean up the downloaded .deb file
        rm "${DEB_FILE}"
    fi
    # Make it executable
    chmod +x "${VENV_BIN}/chromedriver"
else
    # For other platforms, we get chromedriver using the chromedriver_autoinstaller package
    echo -e "\033[0;33mDetecting platform ${OS_TYPE} ${ARCH_TYPE}. Installing chromedriver via chromedriver_autoinstaller...\033[0m"
    # install chromedriver_autoinstaller in the virtual environment
    pip install chromedriver_autoinstaller
    # Create a temp dir to install the chromedriver
    CHROMEDRIVER_DIR_PATH=$(mktemp -d)
    # Use chromedriver_autoinstaller to get the correct chromedriver version
    CHROMEDRIVER_PATH=$(${PYTHON_EXE} -c "import chromedriver_autoinstaller; chromedriver_autoinstaller.install(path='${CHROMEDRIVER_DIR_PATH}')")
    echo "Chromedriver installed at ${CHROMEDRIVER_PATH}. Moving to virtual environment..."
    # NOTE: Here we have to consider Windows cmd and Linux/MacOS bash
    #       also, mv, cp and chmod cmd
    # If Windows
    if [[ "${OS_TYPE}" == "MINGW"* || "${OS_TYPE}" == "CYGWIN"* || "${OS_TYPE}" == "MSYS"* ]]; then
        # Copy the driver
        cp "${CHROMEDRIVER_PATH}" "${VENV_BIN}/chromedriver.exe"
        # Windows doesn't have chmod, skip it
        # Delete the chromedriver_autoinstaller directory to clean up
        rm -rf "${CHROMEDRIVER_DIR_PATH}"
    else
        # Else, for Linux and MacOS
        # Copy the driver
        cp "${CHROMEDRIVER_PATH}" "${VENV_BIN}/chromedriver"
        # Make it executable
        chmod +x "${VENV_BIN}/chromedriver"
        # Delete the chromedriver_autoinstaller directory to clean up
        rm -rf "${CHROMEDRIVER_DIR_PATH}"
    fi
    # Clean up chromedriver_autoinstaller from the virtual environment
    pip uninstall -y chromedriver_autoinstaller
fi

# Final check to ensure chromedriver is in place
# Accepts both chromedriver and chromedriver.exe for Windows
if [[ ! -f "${VENV_BIN}/chromedriver" ]] && [[ ! -f "${VENV_BIN}/chromedriver.exe" ]]; then
    echo "Error: Chromedriver installation failed. Please check the setup script and try again."
    exit 1
fi

# Verbose
echo -e "\n>>> Setup completed >>>"
echo -e "Virtual environment ready. Activate with: \033[0;32msource ${VENV_BIN}/activate\033[0m"
echo -e "To uninstall .venv, simply delete the directory: \033[0;31mrm -rf ${VENV_PATH}\033[0m"
