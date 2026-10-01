#!/bin/sh
set -e

echo "Waiting for postgres at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
until python -c "
import os, socket, sys
host = os.environ.get('POSTGRES_HOST', 'db')
port = int(os.environ.get('POSTGRES_PORT', '5432'))
s = socket.socket()
try:
    s.connect((host, port))
    s.close()
    sys.exit(0)
except OSError:
    sys.exit(1)
"; do
    sleep 1
done
echo "Postgres is up."

echo "Applying migrations..."
alembic upgrade head

echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000