#!/bin/bash

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
LOG_DIR="/var/log/blacklist_module"
INSTALLATION_LOG="$LOG_DIR/install.log"

# Start logging the installation
mkdir -p "$LOG_DIR"
log() {
    echo "$(date '+%F %T') - $*" | tee -a "$INSTALLATION_LOG"
}

# Validate necessary commands
check_commands() {
    for cmd in python3 pip3 sudo apt-get; do
        if ! command -v "$cmd" >/dev/null; then
            log "Error: Required command '$cmd' not found."
            exit 1
        fi
    done
}

install_system_dependencies() {
    log "Installing system dependencies from $DEPENDENCIES_PATH"
    if [[ ! -f "$DEPENDENCIES_PATH" ]]; then
        log "Error: Missing file $DEPENDENCIES_PATH"
        exit 1
    fi

    while IFS= read -r pkg; do
        [[ -z "$pkg" || "$pkg" =~ ^# ]] && continue
        log "Installing: $pkg"
        sudo apt-get install -y "$pkg"
    done < "$DEPENDENCIES_PATH"
}

install_python_dependencies() {
    log "Installing Python packages from $REQUIREMENTS_PATH"
    if [[ ! -f "$REQUIREMENTS_PATH" ]]; then
        log "Error: Missing file $REQUIREMENTS_PATH"
        exit 1
    fi

    pip3 install --upgrade pip
    pip3 install -r "$REQUIREMENTS_PATH"
}

create_app_directories() {
    log "Creating application directories"
    mkdir -p /opt/blacklist_module/api
    mkdir -p /opt/blacklist_module/resources/blacklists
    mkdir -p /var/log/blacklist_module
    chown -R "$(whoami)" /opt/blacklist_module /var/log/blacklist_module
}

copy_project_files() {
    log "Copying project files to /opt/blacklist_module/api"
    cp -r "$PROJECT_DIR"/api/* /opt/blacklist_module/api/
    cp -r "$PROJECT_DIR"/resources/blacklist_sources.txt /opt/blacklist_module/resources/
    cp -r "$PROJECT_DIR"/resources/blacklist_ips.txt /opt/blacklist_module/resources/blacklists/
}

create_service() {
    log "Creating systemd service"
    cp -r "$PROJECT_DIR"/resources/blacklist_module.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable blacklist-monitor
}

main() {
    log "Starting Blacklist Module installation"
    check_commands
    sudo apt-get update
    create_app_directories
    copy_project_files
    install_system_dependencies
    install_python_dependencies
    create_service
    log "Installation complete"
}

main "$@"


echo "[+] Monitoring service status"
systemctl status blacklist-monitor --no-pager

echo "[+] Setup complete"
