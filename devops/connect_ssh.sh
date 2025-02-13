# Source the configuration file
source "$(dirname "$0")/config.sh"

# SSH to the instance using IP address and SSH certificate
ssh -i "$SSH_CERTIFICATE_PATH" "$USER_NAME@$IP_ADDRESS"
