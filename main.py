"""
VRPTW (Vehicle Routing Problem with Time Windows) Application
Main entry point for the PyQt6 application
"""
import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    """Initialize and run the application"""
    app = QApplication(sys.argv)
    app.setApplicationName("VRPTW Route Planner")
    app.setOrganizationName("RoutePlanner")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
