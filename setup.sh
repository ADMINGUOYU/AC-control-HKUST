#!/usr/bin/env bash

# This script sets up a Python virtual environment for the project, 
# installs dependencies, and preinstalls chromedriver for Selenium tests. 

# Set strict mode for better error handling
set -euo pipefail

# Color codes for output
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Get the absolute path to the project root directory
PROJECT_ROOT="$(cd -- "$(dirname "$0")" && pwd)"
VENV_PATH="${PROJECT_ROOT}/.venv"

# Determine OS and architecture
OS_TYPE="$(uname -s)"
ARCH_TYPE="$(uname -m)"

# Normalize OS detection
is_windows() {
    [[ "${OS_TYPE}" == "MINGW"* || "${OS_TYPE}" == "CYGWIN"* || "${OS_TYPE}" == "MSYS"* ]]
}

is_macos() {
    [[ "${OS_TYPE}" == "Darwin" ]]
}

is_linux() {
    [[ "${OS_TYPE}" == "Linux" ]]
}

is_arm() {
    [[ "${ARCH_TYPE}" == "aarch64" || "${ARCH_TYPE}" == "arm64" ]]
}

# Set virtual environment binary path
if is_windows; then
    VENV_BIN="${VENV_PATH}/Scripts"
    CHROMEDRIVER_NAME="chromedriver.exe"
else
    VENV_BIN="${VENV_PATH}/bin"
    CHROMEDRIVER_NAME="chromedriver"
fi

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create virtual environment
log_info "Creating Python virtual environment at ${VENV_PATH}..."
python -m venv "${VENV_PATH}"

# Verify virtual environment creation
if [[ ! -f "${VENV_BIN}/activate" ]]; then
    log_error "Virtual environment activation script not found."
    exit 1
fi

# Activate virtual environment
source "${VENV_BIN}/activate"

# Upgrade pip and install dependencies
log_info "Upgrading pip..."
pip install --upgrade pip

log_info "Installing dependencies from requirements.txt..."
pip install -r "${PROJECT_ROOT}/requirements.txt"

# Install chromedriver based on platform
install_chromedriver() {
    if is_linux && is_arm; then
        install_chromedriver_linux_arm
    else
        install_chromedriver_selenium
    fi
}

install_chromedriver_linux_arm() {
    log_warn "Detected Linux ARM architecture. Installing chromedriver via apt..."

    # Check if apt is available
    if ! command -v apt &> /dev/null; then
        log_error "apt package manager not found. Please install chromedriver manually."
        exit 1
    fi

    # Check for Chromium browser
    local chrome_cmd=""
    if command -v chromium-browser &> /dev/null; then
        chrome_cmd="chromium-browser"
    elif command -v chromium &> /dev/null; then
        chrome_cmd="chromium"
    else
        log_error "Chromium browser not found. Please install Chromium first."
        exit 1
    fi

    # Get Chromium version
    local chrome_version=$("${chrome_cmd}" --version 2>/dev/null | awk '{print $NF}')
    log_info "Detected Chrome/Chromium version: ${chrome_version}"

    # Try to download matching chromedriver
    local major_version=$(echo "${chrome_version}" | cut -d. -f1)
    if apt download "chromium-driver=${chrome_version}*" 2>/dev/null || \
       apt download "chromium-driver=${major_version}*" 2>/dev/null; then
        
        # Extract chromedriver from .deb file
        local deb_file
        deb_file=$(find . -maxdepth 1 -name "chromium-driver_*.deb" -print -quit)
        
        if [[ -f "${deb_file}" ]]; then
            log_info "Extracting chromedriver from ${deb_file}..."
            dpkg-deb --fsys-tarfile "${deb_file}" | tar -xOf - ./usr/bin/chromedriver > "${VENV_BIN}/${CHROMEDRIVER_NAME}"
            chmod +x "${VENV_BIN}/${CHROMEDRIVER_NAME}"
            rm "${deb_file}"
            log_info "Chromedriver installed successfully"
            return 0
        fi
    fi

    # Fallback: check for system-wide chromedriver
    if command -v chromedriver &> /dev/null; then
        log_warn "No matching chromedriver in apt. Using system chromedriver."
        cp "$(command -v chromedriver)" "${VENV_BIN}/${CHROMEDRIVER_NAME}"
        chmod +x "${VENV_BIN}/${CHROMEDRIVER_NAME}"
        log_info "Chromedriver copied from system"
        return 0
    fi

    log_error "Failed to install chromedriver. Please install manually and re-run this script."
    exit 1
}

install_chromedriver_selenium() {
    log_info "Detecting platform: ${OS_TYPE} ${ARCH_TYPE}"
    log_info "Installing chromedriver via selenium..."

    # Set selenium cache directory
    SE_CACHE_PATH="${VENV_PATH}/.cache/selenium"

    # Pip install webdriver-manager
    pip install webdriver-manager

    # Get chromedriver path from selenium
    local chromedriver_path
    chromedriver_path=$(python -c "from webdriver_manager.core.driver_cache import DriverCacheManager; from webdriver_manager.chrome import ChromeDriverManager; custom_path = '${SE_CACHE_PATH}'; manager = DriverCacheManager(root_dir=custom_path); print(ChromeDriverManager(cache_manager=manager).install())" 2>/dev/null)

    if [[ -z "${chromedriver_path}" ]]; then
        log_error "Failed to locate chromedriver using selenium."
        exit 1
    fi

    log_info "Found chromedriver at: ${chromedriver_path}"

    # Copy chromedriver to virtual environment
    if [[ -f "${chromedriver_path}" ]]; then
        cp "${chromedriver_path}" "${VENV_BIN}/${CHROMEDRIVER_NAME}"
        
        # Make executable on Unix-like systems
        if ! is_windows; then
            chmod +x "${VENV_BIN}/${CHROMEDRIVER_NAME}"
        fi
        
        log_info "Chromedriver copied to virtual environment"
    else
        log_error "Chromedriver file not found at expected location."
        exit 1
    fi

    # Clean up selenium cache
    rm -rf "${VENV_PATH}/.cache/selenium"

    # Uninstall webdriver-manager
    pip uninstall -y webdriver-manager
}

# Main chromedriver installation
log_info "Installing chromedriver..."
install_chromedriver

# Verify chromedriver installation
if [[ ! -f "${VENV_BIN}/${CHROMEDRIVER_NAME}" ]]; then
    log_error "Chromedriver installation failed."
    exit 1
fi

# Final success message
echo ""
log_info ">>> Setup completed successfully >>>"
echo -e "Virtual environment ready. Activate with: ${GREEN}source ${VENV_BIN}/activate${NC}"
echo -e "To remove .venv, simply run: ${RED}rm -rf ${VENV_PATH}${NC}"