#!/bin/bash

# Exit on any error
set -e

echo "Running database migrations..."
alembic upgrade head

# Seed database with initial data (idempotent - safe to run multiple times)
echo "Seeding database with initial data..."
python -m app.database.seed_data

echo "Starting server..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}

