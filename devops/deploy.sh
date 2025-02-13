#!/bin/bash

# Source the configuration file
source "$(dirname "$0")/config.sh"

CODE_DIR=$REMOTE_DIR

# Update rsync command to use the SSH certificate
rsync -avz --no-perms --omit-dir-times --exclude='__pycache__' --exclude='.DS_Store' --exclude='.venv/*' --exclude='.vscode' --exclude='.venv' --exclude='.git' --exclude='*.sqlite'  --exclude='.env*' --exclude='pdf-data/*' --exclude='*/ssh/*' -e "ssh -i $SSH_CERTIFICATE_PATH" $LOCAL_DIR $USER_NAME@$IP_ADDRESS:$CODE_DIR


# Update rsync command for pyproject.toml to use the SSH certificate
rsync -avz -e "ssh -i $SSH_CERTIFICATE_PATH" "$LOCAL_DIR/.env.prod" $USER_NAME@$IP_ADDRESS:$REMOTE_DIR/.env

# Update rsync command for pyproject.toml to use the SSH certificate
rsync -avz -e "ssh -i $SSH_CERTIFICATE_PATH" "$LOCAL_DIR/pyproject.toml" $USER_NAME@$IP_ADDRESS:$REMOTE_DIR

ssh -i $SSH_CERTIFICATE_PATH root@$IP_ADDRESS << EOF
cd $REMOTE_DIR
sudo pdm install
sudo systemctl restart rmr
EOF

echo "Files synced and application restarted."
