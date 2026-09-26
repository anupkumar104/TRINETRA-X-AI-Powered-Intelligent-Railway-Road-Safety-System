# AI Safety System

AI-Based Multi-Mode Animal Detection, Track/Road Monitoring & Collision Alert System.

## Current stage

This is Stage 1:
- Flask application
- SQLite database
- Project folders
- Basic dashboard
- Configuration file

## Modes

1. Railway Mode
   - Specific Zone Camera
   - Train Front Camera
   - Future track anomaly analysis

2. Road Mode
   - Specific Zone Camera
   - Vehicle Front Camera

## Setup

Create a virtual environment:

Windows:
    python -m venv .venv
    .venv\Scripts\activate

Install dependencies:

    pip install -r requirements.txt

Run:

    python app.py

Open:

    http://127.0.0.1:5000

## Next stage

Add YOLO video detection, snapshots, virtual danger zones, event correlation and risk engine.
