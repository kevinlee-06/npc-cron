#!/bin/bash

# Configuration
PROJECT_DIR=$(pwd)
SERVICE_NAME="npcron"
SERVICE_USER=$(whoami)
SERVICE_GROUP=$(id -gn)
VENV_DIR="$PROJECT_DIR/.venv"
PYTHON_BIN="$VENV_DIR/bin/python"
UVICORN_BIN="$VENV_DIR/bin/uvicorn"
REQUIREMENTS_FILE="$PROJECT_DIR/backend/requirements.txt"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

echo "Setting up $SERVICE_NAME..."

# Step 1: Check requirements and create virtual environment
echo "Checking dependencies..."
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed."
    exit 1
fi

# Check for venv/pip system packages
if ! python3 -m venv --help &> /dev/null; then
    echo "Error: python3-venv is not installed."
    echo "Run: sudo apt-get install python3-venv"
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR" || {
        echo "Error: Failed to create virtual environment."
        exit 1
    }
fi

# Step 2: Install dependencies
echo "Installing dependencies..."
# Ensure pip is actually there (useful on some Linux distros)
"$PYTHON_BIN" -m ensurepip --upgrade &> /dev/null || echo "Info: ensurepip not found, skipping..."

"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install -r "$REQUIREMENTS_FILE"

# Step 3: Create systemd service file
echo "Generating systemd service file..."
cat <<EOF > "$PROJECT_DIR/$SERVICE_NAME.service"
[Unit]
Description=NPC-Cron Backend Service
After=network.target

[Service]
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$PROJECT_DIR/backend
Environment="PYTHONPATH=$PROJECT_DIR/backend"
ExecStart=$UVICORN_BIN main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Step 4: Install service file to systemd
echo "Installing service to /etc/systemd/system/ (requires sudo)..."
sudo mv "$PROJECT_DIR/$SERVICE_NAME.service" "$SERVICE_FILE"

# Step 5: Reload and start service
echo "Starting service..."
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

# Step 6: Verify status
echo "Verifying service status..."
sudo systemctl status "$SERVICE_NAME" --no-pager

echo ""
echo "Setup complete! You can view logs with: journalctl -u $SERVICE_NAME -f"
echo "Your app is running at http://localhost:8000"
