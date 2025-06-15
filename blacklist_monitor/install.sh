#!/bin/bash

# Validate if script is running with necessary permission
if [[ "$EUID" -ne 0 ]]; then
  echo "Please run as root (e.g., sudo ./install.sh)"
  exit 1
fi

# Enable strict mode
set -euo pipefail
IFS=$'\n\t'

# Paths
PROJECT_DIR="$(dirname "$(realpath "$0")")"
RESOURCES_DIR="$PROJECT_DIR/resources"
DEPENDENCIES_PATH="$RESOURCES_DIR/dependencies.txt"
REQUIREMENTS_PATH="$RESOURCES_DIR/requirements.txt"
PYTHON_VENV_DIR="/opt/blacklist_monitor/venv"
LOG_DIR="/var/log/blacklist_monitor"
INSTALLATION_LOG="$LOG_DIR/install.log"
    
# Start logging the installation
mkdir -p "$LOG_DIR"
log() {
    echo "$(date '+%F %T') - $*" | tee -a "$INSTALLATION_LOG"
}

# Validate necessary commands
check_commands() {
    for cmd in python3 pip3 sudo apt; do
        if ! command -v "$cmd" >/dev/null; then
            log "Error: Required command '$cmd' not found."
            exit 1
        fi
    done
}

# Install system dependencies - apt
install_system_dependencies() {
    log "Installing system dependencies from $DEPENDENCIES_PATH"
    if [[ ! -f "$DEPENDENCIES_PATH" ]]; then
        log "Error: Missing file $DEPENDENCIES_PATH"
        exit 1
    fi

    while IFS= read -r pkg; do
        [[ -z "$pkg" || "$pkg" =~ ^# ]] && continue
        log "Installing: $pkg"
        sudo apt install -y "$pkg"
    done < "$DEPENDENCIES_PATH"
}

# Install python dependencies - pip
install_python_dependencies() {
    log "Installing Python packages from $REQUIREMENTS_PATH"
    if [[ ! -f "$REQUIREMENTS_PATH" ]]; then
        log "Error: Missing file $REQUIREMENTS_PATH"
        exit 1
    fi

    log "Creating virtual environment at $PYTHON_VENV_DIR"
    python3 -m venv "$PYTHON_VENV_DIR"

    source "$PYTHON_VENV_DIR/bin/activate"

    pip install --upgrade pip
    pip install -r "$REQUIREMENTS_PATH"
}

# Create necessary directories
create_app_directories() {
    log "Creating application directories"
    mkdir -p /opt/blacklist_monitor/api
    mkdir -p /opt/blacklist_monitor/resources/blacklists
    mkdir -p /var/log/blacklist_monitor
    chown -R "$(whoami)" /opt/blacklist_monitor /var/log/blacklist_monitor
}

# Copy project files
copy_project_files() {
    log "Copying project files to /opt/blacklist_monitor/api"
    cp -r "$PROJECT_DIR"/api/* /opt/blacklist_monitor/api/
    cp -r "$PROJECT_DIR"/resources/blacklist_sources.txt /opt/blacklist_monitor/resources/
    cp -r "$PROJECT_DIR"/resources/blacklist_ips.txt /opt/blacklist_monitor/resources/blacklists/
}

# Enable services
create_services() {
    log "Creating systemd service"
    cp "$PROJECT_DIR"/resources/blacklist_monitor.service /etc/systemd/system/
    cp "$PROJECT_DIR"/resources/blacklist_notifier.service /etc/systemd/system/
    log "Enabling services"
    systemctl daemon-reload
    systemctl enable blacklist_monitor
    systemctl enable blacklist_notifier
}

main() {
    log "Starting Blacklist Monitor installation"
    check_commands
    sudo apt-get update
    create_app_directories
    copy_project_files
    install_system_dependencies
    install_python_dependencies
    create_services
    log "Installation complete"
}

main "$@"

echo "[+] Monitoring service status"
systemctl status blacklist_monitor --no-pager

echo "[+] Setup complete"
