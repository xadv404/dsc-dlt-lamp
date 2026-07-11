#!/usr/bin/env bash
set -euo pipefail

VENV_DIR="venv"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Fix venv — dsc-dlt-lamp ==="
echo ""

install_system_deps() {
    echo "[*] Installation des paquets système pour venv..."

    if command -v apt &>/dev/null; then
        sudo apt update -y
        sudo apt install -y python3 python3-pip python3-venv python3-full
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y python3 python3-pip
    elif command -v yum &>/dev/null; then
        sudo yum install -y python3 python3-pip
    else
        echo "[!] Gestionnaire de paquets non reconnu."
        echo "    Installe manuellement : python3, python3-pip, python3-venv"
        exit 1
    fi
}

check_python() {
    if ! command -v python3 &>/dev/null; then
        echo "[!] python3 introuvable."
        install_system_deps
    fi

    echo "[+] Python : $(python3 --version)"
}

check_venv_package() {
    if ! python3 -m venv --help &>/dev/null; then
        echo "[!] Le module venv n'est pas disponible."
        install_system_deps
    fi

    # Test réel de création (détecte ensurepip manquant)
    local test_dir
    test_dir="$(mktemp -d)"
    if ! python3 -m venv "$test_dir" &>/dev/null; then
        rm -rf "$test_dir"
        echo "[!] python3-venv / ensurepip manquant."
        install_system_deps
    fi
    rm -rf "$test_dir"
    echo "[+] Module venv OK"
}

remove_broken_venv() {
    if [ -d "$VENV_DIR" ]; then
        echo "[*] Suppression de l'ancien venv..."
        rm -rf "$VENV_DIR"
    fi
}

create_venv() {
    echo "[*] Création du venv..."
    if ! python3 -m venv "$VENV_DIR"; then
        echo "[!] Échec création venv, tentative avec --without-pip..."
        python3 -m venv --without-pip "$VENV_DIR"
        source "$VENV_DIR/bin/activate"
        curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
        python /tmp/get-pip.py
        rm -f /tmp/get-pip.py
        return
    fi
}

activate_venv() {
    if [ ! -f "$VENV_DIR/bin/activate" ]; then
        echo "[!] Fichier $VENV_DIR/bin/activate introuvable."
        echo "    Le venv est corrompu. Relance : ./fix-venv.sh"
        exit 1
    fi

    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    echo "[+] venv activé : $(which python)"
}

install_deps() {
    echo "[*] Installation des dépendances..."
    python -m pip install --upgrade pip

    if [ -f "pyproject.toml" ]; then
        pip install .
    elif [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        pip install requests rich
    fi

    echo "[+] Dépendances installées"
}

verify_install() {
    echo "[*] Vérification..."
    python -c "import requests; import rich; print('[+] requests et rich OK')"
}

# ── Exécution ────────────────────────────────────────────────────────────────
check_python
check_venv_package
remove_broken_venv
create_venv
activate_venv
install_deps
verify_install

echo ""
echo "=== venv réparé avec succès ==="
echo ""
echo "Pour lancer le script :"
echo "  cd $SCRIPT_DIR"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
