#!/bin/sh
# Production startup script for Trace backend

set -e

echo "🚀 Trace Backend - Production Startup"
echo "======================================"

# Get PORT from environment, default to 8000
PORT=${PORT:-8000}

# Check required environment variables
for var in TRACE_SECRET_KEY TRACE_DB_URL TRACE_FRONTEND_ORIGIN; do
  if [ -z "$(eval echo \$$var)" ]; then
    echo "❌ Error: Required environment variable '$var' is not set"
    exit 1
  fi
done

echo "✓ Environment variables validated"

# Run bootstrap to initialize database
echo "📦 Initializing database..."
python -c "from trace.bootstrap import bootstrap; bootstrap()"
echo "✓ Database ready"

# Start server with uvicorn
echo "🔥 Starting Trace API server on port $PORT..."
uvicorn \
  --host 0.0.0.0 \
  --port $PORT \
  --workers 4 \
  trace.api.app:app
