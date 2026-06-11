#!/usr/bin/env bash
# Kraken Audit — Local Dev Server Launcher
# Starts the FastAPI backend + prints frontend instructions.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Load .env if present
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

echo "  🐙 Kraken Audit Dashboard"
echo "  ═══════════════════════════"
echo "  🔧 Starting API server..."
echo ""

PYTHONPATH="$SCRIPT_DIR/.." python3 api_server.py