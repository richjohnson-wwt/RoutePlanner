# VRPTW Route Planner

This application assists the user in solving a route problem. 

It is a PyQt6-based application for solving Vehicle Routing Problems with Time Windows (VRPTW).

The application is driven by a ProblemState object that maintains the state of the problem as it is being solved. Through parsing, geocoding, clustering the sites and solving the route problem.

## Setup

1. Create and activate virtual environment:
```bash
uv venv .venv
source .venv/bin/activate  # On macOS/Linux
```

2. Install dependencies:
```bash
uv add pyqt6
uv add pandas
uv add pyyaml
uv add openpyxl
```

## Running the Application

```bash
python main.py
```

## Project Structure

```
RoutePlanner/
├── main.py              # Application entry point
├── ui/                 # GUI components
│   ├── __init__.py
│   └── main_window.py   # Main application window
├── services/           # Business logic services
├── models/             # Data models
└── README.md           # This file
```

## Features

- PyQt6-based graphical user interface
- VRPTW problem visualization
- Route optimization solver

## Development

This application is under active development. Architecture and features will be added incrementally.
