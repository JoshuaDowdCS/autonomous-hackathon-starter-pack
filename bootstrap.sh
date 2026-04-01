#!/bin/bash
set -e

echo "Starting Hackathon Pipeline Setup..."

echo "1. Installing Python dependencies..."
pip install -r requirements.txt || echo "requirements.txt not found yet, skipping..."

echo "2. Installing Node dependencies for Stagehand and UI..."
if [ -d "ui" ]; then
    cd ui
    npm install
    cd ..
else
    echo "UI folder not found! Make sure to scaffold Vite first."
fi

npm install @browserbasehq/stagehand

echo "3. Seeding SQLite Database..."
python -c "from db.state_store import init_db; init_db()"

echo "Setup complete. You can now run the pipeline with:"
echo "python pipeline/main.py"
