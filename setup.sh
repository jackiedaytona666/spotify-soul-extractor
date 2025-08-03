#!/bin/bash
# Setup script for Spotify Soul Extractor

echo "Setting up Spotify Soul Extractor..."

# check Python
python_version=$(python3 --version 2>/dev/null | cut -d' ' -f2)
if [[ -z "$python_version" ]]; then
    echo "Error: Python 3 not found. Install Python 3.9+"
    exit 1
fi

# Check if Python version is >= 3.9
version_major=$(echo "$python_version" | cut -d. -f1)
version_minor=$(echo "$python_version" | cut -d. -f2)
if (( version_major < 3 )) || { (( version_major == 3 )) && (( version_minor < 9 )); }; then
    echo "Error: Python version $python_version is too old. Install Python 3.9+"
    exit 1
fi

echo "Found Python $python_version"

# create venv if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# activate venv (platform-specific)
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# install dependencies
if [ ! -f ".env" ]; then
    if [ ! -f ".env.example" ]; then
        echo "Error: .env.example file not found. Please provide .env.example before running setup."
        exit 1
    fi
    echo "Creating .env file..."
    cp .env.example .env
    echo ""
    echo "IMPORTANT: Edit .env with your Spotify API credentials"
    echo "Get them from: https://developer.spotify.com/dashboard"
else
    echo ".env file already exists"
fi

echo "Next steps:"
echo "1. Run: python server.py"
echo "2. Open: http://localhost:8889"
echo "Or use Docker: docker-compose up --build"
echo "2. Run: python server.py"
echo "3. Open: http://localhost:8889"
echo ""
