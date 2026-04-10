#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"

if [[ -d ".venv" && -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
elif [[ -d "venv" && -x "venv/bin/python" ]]; then
  PYTHON_BIN="venv/bin/python"
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python 3 bulunamadi. Lütfen Python 3 kurup tekrar dene."
  exit 1
fi

MISSING_MODULES="$("$PYTHON_BIN" - <<'PY'
import importlib.util

required = ["PySide6", "sqlalchemy"]
missing = [module for module in required if importlib.util.find_spec(module) is None]
print(" ".join(missing))
PY
)"

if [[ -n "${MISSING_MODULES// }" ]]; then
  echo "Eksik Python modulleri: $MISSING_MODULES"
  echo "Kurulum:"
  echo "  $PYTHON_BIN -m pip install PySide6 sqlalchemy"
  exit 1
fi

if [[ ! -f "library_v2.db" ]]; then
  echo "Ilk kurulum: veritabani olusturuluyor..."
  "$PYTHON_BIN" setup_db.py
fi

echo "Library Management System baslatiliyor..."
exec "$PYTHON_BIN" main.py
