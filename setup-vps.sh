#!/usr/bin/env bash
set -euo pipefail

echo "=== Setup VPS — dsc-dlt-lamp ==="
echo ""

# ── 1. Python & pip ──────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "[*] Installation de Python3..."
    if command -v apt &>/dev/null; then
        sudo apt update -y
        sudo apt install -y python3 python3-pip python3-venv
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y python3 python3-pip
    elif command -v yum &>/dev/null; then
        sudo yum install -y python3 python3-pip
    else
        echo "[!] Installe Python3 manuellement puis relance ce script."
        exit 1
    fi
fi

echo "[+] Python : $(python3 --version)"

# ── 2. pip à jour ────────────────────────────────────────────────────────────
python3 -m pip install --upgrade pip --break-system-packages 2>/dev/null \
    || python3 -m pip install --upgrade pip

echo "[+] pip : $(python3 -m pip --version)"

# ── 3. Environnement virtuel ─────────────────────────────────────────────────
VENV_DIR="venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "[*] Création de l'environnement virtuel..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install .

echo ""
echo "=== Installation terminée ==="
echo ""
echo "Pour lancer le script :"
echo "  cd $(pwd)"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
echo "Ou en une ligne :"
echo "  cd $(pwd) && source venv/bin/activate && python main.py"
echo ""
echo "N'oublie pas de mettre ton token dans main.py !"
