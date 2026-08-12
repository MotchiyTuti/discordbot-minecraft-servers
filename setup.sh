#!/bin/bash
sudo apt update -y
sudo apt upgrade -y
sudo apt install python3 python3-venv tmux -y


python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt


TOKEN=""

for arg in "$@"; do
    case "$arg" in
        --token=*)
            TOKEN="${arg#--token=}"
            ;;
    esac
done

if [ -n "$TOKEN" ]; then
    echo "$TOKEN" > token.txt
fi
