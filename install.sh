#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Installation de dsc-dlt-lamp..."
exec "$SCRIPT_DIR/fix-venv.sh"
