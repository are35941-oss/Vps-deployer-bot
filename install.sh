#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

if [[ "${EUID}" -eq 0 ]]; then
    if ! command -v apt-get >/dev/null; then
        echo "Automatic system package installation requires Debian or Ubuntu." >&2
        exit 1
    fi
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y python3 python3-venv python3-pip docker.io
    if command -v systemctl >/dev/null && [[ -d /run/systemd/system ]]; then
        systemctl enable --now docker
    fi
else
    echo "Running without root: Python, venv, and an accessible Docker daemon must already be installed."
fi

if [[ ! -f .env ]]; then
    cp .env.example .env
    chmod 600 .env
    echo "Created .env. Set DISCORD_TOKEN and VPS_PUBLIC_HOST, then run this script again."
    exit 1
fi
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
exec .venv/bin/python bot.py