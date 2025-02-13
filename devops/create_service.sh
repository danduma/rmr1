source "$(dirname "$0")/config.sh"

SETUP_SCRIPT_2="#!/bin/bash
cd $REMOTE_DIR

mkdir -p /opt/rmr/
sudo chown -R root:root /opt/rmr/

sudo bash -c 'cat > /etc/systemd/system/rmr.service << EOL
[Unit]
Description=RMR
After=network.target

[Service]
User=root
Group=root
Environment="PYTHONPATH=$REMOTE_DIR"
WorkingDirectory=$REMOTE_DIR
ExecStart=$REMOTE_DIR/.venv/bin/python $REMOTE_DIR/server.py
Restart=always
StandardOutput=journal
StandardError=journal

# Logging
LogLevelMax=debug
SyslogIdentifier=rmr

# Increase open file limit if needed
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOL'
# Enable and start the FastAPI service
sudo systemctl daemon-reload
sudo systemctl enable rmr
sudo systemctl restart rmr"


echo "Running Setup Script 2..."
run_ssh_command "$SETUP_SCRIPT_2"