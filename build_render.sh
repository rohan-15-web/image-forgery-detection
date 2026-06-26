#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install Python backend dependencies
pip install -r requirements.txt

# Build the React frontend
cd frontend
npm install
npm run build
cd ..
