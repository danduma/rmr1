#!/bin/bash

# Variables 
source "$(dirname "$0")/config.sh"

SETUP_SCRIPT_1="#!/bin/bash
sudo apt-get install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3.11-distutils uvicorn python-is-python3 python3-poetry
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
apt-get install -y build-essential python3.11-dev libffi-dev cargo
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install -y caddy

sudo mkdir -p $REMOTE_DIR

# sudo usermod -a -G www-data $(who | awk '{print $1}' | sort -u)
# sudo chown -R www-data:www-data  $REMOTE_DIR
# sudo chmod -R 777  $REMOTE_DIR

curl -sSL https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
pip install pdm uvicorn
pdm install
"



# CADDY 

CADDY_SETUP_SCRIPT="
# Update Caddyfile to serve your application with HTTPS
cat > /etc/caddy/Caddyfile <<EOL
, :80, :443 {
    tls {
        on_demand
    }

    @api {
        path_regexp ^/api/.*
    }

    handle @api {
        reverse_proxy 127.0.0.1:8000
        header Access-Control-Allow-Origin \"https://astra2.cognivita.co\"
        header Access-Control-Allow-Methods \"GET, POST, PUT, DELETE, OPTIONS\"
        header Access-Control-Allow-Headers \"*\"
        header Access-Control-Allow-Credentials \"true\"
    }

    handle {
        reverse_proxy 127.0.0.1:3000
    }
}
EOL
pkill caddy
systemctl restart caddy.service
"


# Run each setup script in a separate SSH command
echo "Running Setup Script 1..."
run_ssh_command "$SETUP_SCRIPT_1"

source "$(dirname "$0")/create_service.sh"

# echo "Updating Caddyfile and restarting Caddy service..."
# run_ssh_command "$CADDY_SETUP_SCRIPT"

