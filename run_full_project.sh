#!/bin/bash
set -e

echo "Installing backend dependencies..."
bash ./backend/install_dependencies.sh

echo "Installing frontend dependencies..."
cd frontend
npm install
cd ..

echo "Starting full project with docker-compose..."
docker-compose up
