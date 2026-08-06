#!/usr/bin/env bash
# Unified launcher for the Agentic Patterns demos.
# Run: ./run.sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

SINGLE_DIR="$ROOT_DIR/Single_Agent_Pattern"
MULTI_DIR="$ROOT_DIR/Multi_Agent_Pattern"

SINGLE_PORT=8501
MULTI_PORT=8502

setup_venv() {
  if [ ! -d "$VENV_DIR" ]; then
    echo "Creating shared virtual environment at .venv ..."
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install --upgrade pip -q
    "$VENV_DIR/bin/pip" install -q \
      -r "$SINGLE_DIR/requirements.txt" \
      -r "$MULTI_DIR/requirements.txt"
    echo "Environment ready."
    echo ""
  fi
}

launch() {
  local dir="$1" port="$2" name="$3"
  echo "Starting $name demo on http://localhost:$port ..."
  cd "$dir"
  exec "$VENV_DIR/bin/streamlit" run app.py --server.port "$port"
}

main() {
  setup_venv

  echo "Which demo would you like to run?"
  echo "  1) Single Agent Patterns   (port $SINGLE_PORT)"
  echo "  2) Multi Agent Patterns    (port $MULTI_PORT)"
  read -rp "Enter choice [1-2]: " choice

  case "$choice" in
    1) launch "$SINGLE_DIR" "$SINGLE_PORT" "Single Agent" ;;
    2) launch "$MULTI_DIR" "$MULTI_PORT" "Multi Agent" ;;
    *) echo "Invalid choice: $choice"; exit 1 ;;
  esac
}

main
