# VRPTW Route Planner

A PyQt6-based application for solving Vehicle Routing Problems with Time Windows (VRPTW).

## Setup

1. Create and activate virtual environment:
```bash
uv venv .venv
source .venv/bin/activate  # On macOS/Linux
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

```bash
python main.py
```

## Project Structure

```
RoutePlanner/
├── main.py              # Application entry point
├── gui/                 # GUI components
│   ├── __init__.py
│   └── main_window.py   # Main application window
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Features

- PyQt6-based graphical user interface
- VRPTW problem visualization
- Route optimization solver

## Development

This application is under active development. Architecture and features will be added incrementally.
