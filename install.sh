#!/usr/bin/env bash
set -e

echo "Installation de dsc-dlt-lamp..."
python3 -m pip install --upgrade pip
python3 -m pip install .

echo ""
echo "Terminé ! Lance avec : discord-deleter"
