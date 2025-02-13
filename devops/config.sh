#!/bin/bash
# Variables 
PROJECT_ID="rmr"
# ZONE="us-central1-a"
# REGION="us-central1"
# INSTANCE_NAME="protocols"
# IP_ADDRESS_NAME="protocols-ip"
# MACHINE_TYPE="s-2vcpu-2gb"
# IMAGE_FAMILY="ubuntu-2204-lts"
# IMAGE_PROJECT="ubuntu-os-cloud"
LOCAL_DIR="$(dirname "$0")/../"
REMOTE_DIR="/opt/rmr"
IP_ADDRESS="49.12.8.100"
SSH_CERTIFICATE_PATH="$(realpath "$(dirname "$0")/ssh/hetzner1")"
USER_NAME="root"


# Function to run SSH command with certificate
run_ssh_command() {
    ssh -o StrictHostKeyChecking=no -i "$SSH_CERTIFICATE_PATH" root@$IP_ADDRESS "$1"
}
