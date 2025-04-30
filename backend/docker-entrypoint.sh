#!/bin/bash
set -e

# Print the Python version
echo "Using Python $(python --version)"

# Check if migrations need to be run
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    echo "Running database migrations..."
    alembic upgrade head
fi

# Create necessary directories if they don't exist
mkdir -p /app/workspaces /app/logs /app/chromadb /app/backups

# Set up proper signal handling for containerized environment
function handle_signal {
    echo "Received signal. Shutting down gracefully..."
    kill -TERM "$child"
    wait "$child"
    exit 0
}

# Register signal handlers
trap handle_signal SIGINT SIGTERM

# Determine number of workers based on CPU cores if not specified
if [ -z "${UVICORN_WORKERS}" ]; then
    CORES=$(grep -c ^processor /proc/cpuinfo 2>/dev/null || echo 1)
    UVICORN_WORKERS=$(( CORES * 2 + 1 ))
    if [ "$UVICORN_WORKERS" -gt 8 ]; then
        UVICORN_WORKERS=8
    fi
    echo "Setting worker count to $UVICORN_WORKERS based on $CORES CPU cores"
fi

# Execute the command
echo "Starting application..."
exec "$@" &

# Store the PID of the child process
child=$!

# Wait for the child process to terminate
wait "$child" 