#!/usr/bin/env bash
# Production startup script for Trace backend

set -e

echo "🚀 Trace Backend - Production Startup"
echo "======================================"

# Check required environment variables
required_vars=("TRACE_SECRET_KEY" "TRACE_DB_URL" "TRACE_FRONTEND_ORIGIN")

for var in "${required_vars[@]}"; do
  if [ -z "${!var}" ]; then
    echo "❌ Error: Required environment variable '$var' is not set"
    exit 1
  fi
done

echo "✓ Environment variables validated"

# Run migrations / bootstrap
echo "📦 Initializing database..."
python -c "from trace.bootstrap import bootstrap; bootstrap()"
echo "✓ Database ready"

# Start server
echo "🔥 Starting Trace API server..."
gunicorn \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:${PORT:-8000} \
  --timeout 60 \
  --access-logfile - \
  --error-logfile - \
  trace.api.app:app
