#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f "$SCRIPT_DIR/fix-venv.sh" ]; then
    exec "$SCRIPT_DIR/fix-venv.sh"
fi

echo "[!] fix-venv.sh introuvable."
exit 1
