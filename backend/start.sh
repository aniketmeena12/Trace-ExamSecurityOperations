#!/bin/sh
# Production startup script for Trace backend

set -e

echo "🚀 Trace Backend - Production Startup"
echo "======================================"

# Get PORT from environment, default to 8000
PORT=${PORT:-8000}

# Set default TRACE_SECRET_KEY if missing (dev only - should be set in production)
TRACE_SECRET_KEY=${TRACE_SECRET_KEY:-"dev-insecure-key-change-in-production"}

# Try to get PostgreSQL URL from Railway's automatic variable
if [ -z "$TRACE_DB_URL" ] && [ -n "$DATABASE_URL" ]; then
  TRACE_DB_URL=$DATABASE_URL
  echo "ℹ️  Using DATABASE_URL from PostgreSQL service"
fi

# Set default TRACE_DB_URL if still missing
TRACE_DB_URL=${TRACE_DB_URL:-"sqlite:///./trace.db"}

# Set default TRACE_FRONTEND_ORIGIN
TRACE_FRONTEND_ORIGIN=${TRACE_FRONTEND_ORIGIN:-"http://localhost:5173"}

echo "✓ Environment configuration:"
echo "  - Database: ${TRACE_DB_URL:0:50}..."
echo "  - Frontend Origin: $TRACE_FRONTEND_ORIGIN"
echo "  - Port: $PORT"

# Run bootstrap to initialize database
echo "📦 Initializing database..."
python -c "from trace.bootstrap import bootstrap; bootstrap()"
echo "✓ Database ready"

# Start server with uvicorn
echo "🔥 Starting Trace API server on port $PORT..."
uvicorn \
  --host 0.0.0.0 \
  --port $PORT \
  trace.api.app:app
