#!/bin/sh
# Production startup script for Trace backend

set -e

echo "🚀 Trace Backend - Production Startup"
echo "======================================"

# Host platform (Render, Railway, ...) injects PORT; fall back for local runs.
PORT=${PORT:-8000}

# Defaults below are dev-only. Exported so the Python process actually sees
# them — a plain assignment stays in this shell and never reaches uvicorn.
export TRACE_SECRET_KEY=${TRACE_SECRET_KEY:-"dev-insecure-key-change-in-production"}

# Managed PostgreSQL add-ons expose DATABASE_URL; use it when TRACE_DB_URL
# wasn't set explicitly.
if [ -z "$TRACE_DB_URL" ] && [ -n "$DATABASE_URL" ]; then
  TRACE_DB_URL=$DATABASE_URL
  echo "ℹ️  Using DATABASE_URL from PostgreSQL service"
fi

# postgres:// / postgresql:// are normalized to the psycopg driver in
# trace/config.py, so every entrypoint (this script, gunicorn) gets it.
export TRACE_DB_URL=${TRACE_DB_URL:-"sqlite:///./trace.db"}
export TRACE_FRONTEND_ORIGIN=${TRACE_FRONTEND_ORIGIN:-"http://localhost:5173"}

# Log the driver only — the full URL carries the database password.
echo "✓ Environment configuration:"
echo "  - Database: $(echo "$TRACE_DB_URL" | cut -d: -f1)"
echo "  - Frontend Origin: $TRACE_FRONTEND_ORIGIN"
echo "  - Port: $PORT"

# Run bootstrap to initialize database
echo "📦 Initializing database..."
python -c "from trace.bootstrap import bootstrap; bootstrap()"
echo "✓ Database ready"

# Start server with uvicorn
echo "🔥 Starting Trace API server on port $PORT..."
exec uvicorn \
  --host 0.0.0.0 \
  --port "$PORT" \
  trace.api.app:app
