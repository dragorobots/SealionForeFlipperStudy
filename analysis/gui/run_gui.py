#!/usr/bin/env python3
"""
Simple launcher script for the Full-Stroke Overview Metrics GUI
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the GUI
from full_stroke_overview_gui import main

if __name__ == "__main__":
    main()

