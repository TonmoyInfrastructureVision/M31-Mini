#!/bin/bash

# Bash script to install python dependencies on Arch Linux without using virtual environment

set -e

REQUIREMENTS_FILE="requirements.txt"
PYTHON_BIN="/usr/bin/python"
PIP_BIN="/usr/bin/pip"

# Check if running on Arch Linux by checking pacman existence
if ! command -v pacman &> /dev/null
then
    echo "Error: pacman package manager not found. This script is intended for Arch Linux."
    exit 1
fi

# Update package database
echo "Updating package database..."
sudo pacman -Sy

# Install python if not installed
if ! command -v $PYTHON_BIN &> /dev/null
then
    echo "Python not found. Installing python..."
    sudo pacman -S --noconfirm python
else
    echo "Python is already installed."
fi

# Install python-pip if not installed
if ! command -v $PIP_BIN &> /dev/null
then
    echo "pip not found. Installing python-pip..."
    sudo pacman -S --noconfirm python-pip
else
    echo "pip is already installed."
fi

# Upgrade pip
echo "Upgrading pip..."
sudo $PIP_BIN install --upgrade pip

# Install dependencies from requirements.txt
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing dependencies from $REQUIREMENTS_FILE..."
    sudo $PIP_BIN install -r $REQUIREMENTS_FILE
else
    echo "Error: $REQUIREMENTS_FILE not found."
    exit 1
fi

echo "All dependencies installed successfully."
