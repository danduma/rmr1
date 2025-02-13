#!/bin/bash

# Source the configuration file
source "$(dirname "$0")/config.sh"

REMOTE_DIR="/opt/rmr_pictures"
LOCAL_DIR='/Users/masterman/Downloads/LEVF/Whole body pictures/processed_images'

# Update rsync command to use the SSH certificate
rsync -avz --no-perms --omit-dir-times --exclude='__pycache__' --exclude='.DS_Store' --exclude='.venv/*' --exclude='.vscode' --exclude='.venv' --exclude='.git' --exclude='*.sqlite'  --exclude='.env*' --exclude='pdf-data/*' --exclude='*/ssh/*' -e "ssh -i $SSH_CERTIFICATE_PATH" "$LOCAL_DIR" "$USER_NAME@$IP_ADDRESS:$REMOTE_DIR"

