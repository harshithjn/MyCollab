#!/bin/bash

echo "Starting MyCollab..."

if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "Warning: Python $PYTHON_VERSION detected. Python 3.11+ is recommended."
fi

echo "Python version: $PYTHON_VERSION"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies..."
cd backend
pip install --upgrade pip
pip install -r requirements.txt

echo "Starting FastAPI backend server..."
echo "Backend API: http://localhost:8000"
echo "Frontend: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "To stop the server, press Ctrl+C"
echo ""

python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

cleanup() {
    echo ""
    echo "Stopping server..."
    echo "Server stopped!"
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "MyCollab is now running!"
echo ""
echo "Application: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Open your browser and go to http://localhost:8000 to start collaborating!"
echo ""

wait