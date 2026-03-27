#!/bin/bash

# Configuration
PROJECT_DIR=$(pwd)
SERVICE_NAME="npcron"
VENV_DIR="$PROJECT_DIR/.venv"
PYTHON_BIN="$VENV_DIR/bin/python"
UVICORN_BIN="$VENV_DIR/bin/uvicorn"
REQUIREMENTS_FILE="$PROJECT_DIR/backend/requirements.txt"
USER_SYSTEMD_DIR="$HOME/.config/systemd/user"
SERVICE_FILE="$USER_SYSTEMD_DIR/$SERVICE_NAME.service"

echo "Setting up $SERVICE_NAME as a User Service..."

# Step 0: Clean up old system-level service if it exists (requires sudo)
if [ -f "/etc/systemd/system/$SERVICE_NAME.service" ]; then
    echo "Removing legacy system-level service..."
    sudo systemctl stop "$SERVICE_NAME" &> /dev/null
    sudo systemctl disable "$SERVICE_NAME" &> /dev/null
    sudo rm "/etc/systemd/system/$SERVICE_NAME.service"
    sudo systemctl daemon-reload
fi

# Step 1: Check requirements and create virtual environment
echo "Checking dependencies..."
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed."
    exit 1
fi

if ! python3 -m venv --help &> /dev/null; then
    echo "Error: python3-venv is not installed."
    echo "Run: sudo apt-get install python3-venv"
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR" || { echo "Error: Failed to create venv."; exit 1; }
fi

# Step 2: Install dependencies
echo "Installing dependencies..."
"$PYTHON_BIN" -m ensurepip --upgrade &> /dev/null
"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install -r "$REQUIREMENTS_FILE"

# Step 3: Create user systemd directory
mkdir -p "$USER_SYSTEMD_DIR"

# Step 4: Create systemd user service file
echo "Generating systemd user service file..."
cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=NPC-Cron User Backend Service (with Audio Access)
After=network.target

[Service]
WorkingDirectory=$PROJECT_DIR/backend
Environment="PYTHONPATH=$PROJECT_DIR/backend"
# Inherit common user environment variables for audio
Environment="XDG_RUNTIME_DIR=/run/user/$(id -u)"
ExecStart=$UVICORN_BIN main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

# Step 5: Enable linger to keep service running after logout
echo "Enabling linger for $(whoami)..."
sudo loginctl enable-linger "$(whoami)"

# Step 6: Reload and start user service
echo "Starting user service..."
systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME"
systemctl --user restart "$SERVICE_NAME"

# Step 7: Verify status
echo "Verifying user service status..."
systemctl --user status "$SERVICE_NAME" --no-pager

echo ""
echo "Setup complete! The service is now running in your USER session."
echo "This ensures access to PulseAudio/PipeWire for sound playback."
echo "View logs with: journalctl --user -u $SERVICE_NAME -f"
echo "URL: http://localhost:8000"
