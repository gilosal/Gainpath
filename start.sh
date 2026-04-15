#!/usr/bin/env bash
set -e

# Run database migrations
echo "==> Running database migrations"
cd /app/backend
python -m alembic upgrade head

# Start backend (FastAPI) in background
echo "==> Starting backend on port ${PORT:-8000}"
python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" &
BACKEND_PID=$!

# Start frontend (Next.js standalone) in background
echo "==> Starting frontend on port 3000"
cd /app/frontend
if [ -d ".next/standalone" ]; then
  cd .next/standalone
  PORT=3000 node server.js &
else
  PORT=3000 npm run start &
fi
FRONTEND_PID=$!

# Wait for either process to exit
wait -n $BACKEND_PID $FRONTEND_PID
EXIT_CODE=$?

# If one exits, kill the other
kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
exit $EXIT_CODE
