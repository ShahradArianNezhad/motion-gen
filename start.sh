#!/usr/bin/env bash
# One-command local development: install what's missing, then run the API and studio.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

WEB_PORT="${WEB_PORT:-5173}"
VENV="$ROOT/.venv"
PYTHON="$VENV/bin/python"
API_PID=""
WEB_PID=""

command -v node >/dev/null || { echo "Node.js 20+ is required." >&2; exit 1; }
command -v python3 >/dev/null || { echo "Python 3.10+ is required." >&2; exit 1; }

cleanup() {
  trap - EXIT INT TERM
  for pid in "$WEB_PID" "$API_PID"; do
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
    fi
  done
  wait 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# Frontend dependencies: reinstall if the lockfile changed since the last install.
if [ ! -x "$ROOT/node_modules/.bin/vite" ] || [ ! -f "$ROOT/node_modules/.package-lock.json" ] || [ "$ROOT/package-lock.json" -nt "$ROOT/node_modules/.package-lock.json" ]; then
  echo "Installing frontend dependencies..."
  npm ci --no-audit --no-fund
fi

# Backend environment and dependencies.
if [ ! -x "$PYTHON" ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv "$VENV"
fi
REQUIREMENTS_HASH="$(cksum backend/requirements.txt | cut -d ' ' -f 1)"
if [ ! -f "$VENV/.requirements-hash" ] || [ "$(cat "$VENV/.requirements-hash")" != "$REQUIREMENTS_HASH" ]; then
  echo "Installing Python dependencies..."
  "$PYTHON" -m pip install --disable-pip-version-check -r backend/requirements.txt
  printf '%s' "$REQUIREMENTS_HASH" > "$VENV/.requirements-hash"
fi

echo "Starting API on http://localhost:8000 (docs: http://localhost:8000/docs)"
"$PYTHON" -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 &
API_PID=$!

echo "Starting Motion Studio on http://localhost:$WEB_PORT"
"$ROOT/node_modules/.bin/vite" --host 0.0.0.0 --port "$WEB_PORT" &
WEB_PID=$!

echo "Press Ctrl+C to stop both servers."
set +e
# wait -n needs Bash 4.3+; older shells (e.g. macOS default Bash 3) just wait on Vite.
if [ "${BASH_VERSINFO[0]:-0}" -gt 4 ] || { [ "${BASH_VERSINFO[0]:-0}" -eq 4 ] && [ "${BASH_VERSINFO[1]:-0}" -ge 3 ]; }; then
  wait -n "$API_PID" "$WEB_PID"
else
  wait "$WEB_PID"
fi
status=$?
set -e
exit "$status"
