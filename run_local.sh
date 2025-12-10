#!/bin/bash

# Flight Tracker - Local Development Startup Script (Kepler.gl version)

echo "🚀 Starting Flight Tracker Application with Kepler.gl..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r app/requirements.txt

# Check for required Databricks environment variables
if [ -z "$DATABRICKS_SERVER_HOSTNAME" ] || [ -z "$DATABRICKS_HTTP_PATH" ] || [ -z "$DATABRICKS_TOKEN" ]; then
    echo ""
    echo "⚠️  WARNING: Databricks credentials not configured!"
    echo ""
    echo "Please set the following environment variables:"
    echo "  export DATABRICKS_SERVER_HOSTNAME=\"your-workspace.cloud.databricks.com\""
    echo "  export DATABRICKS_HTTP_PATH=\"/sql/1.0/warehouses/your-warehouse-id\""
    echo "  export DATABRICKS_TOKEN=\"your-databricks-token\""
    echo ""
    echo "See DATABRICKS_SETUP.md for detailed instructions."
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Set default environment variables if not set
export PORT="${PORT:-8050}"
export HOST="${HOST:-0.0.0.0}"

echo ""
echo "✅ Setup complete!"
echo "📊 Starting application on http://localhost:${PORT}"
echo "🗺️  Using Kepler.gl for animated flight visualization"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

# Run the application
cd app
python app.py

