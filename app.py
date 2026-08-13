#!/usr/bin/env python3
"""
CS402.3 Student Attendance Management System (SAMS)
Dual Launcher: Starts Web Dashboard Server + Launches Browser Interface
Usage: python app.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web_server import start_server

if __name__ == '__main__':
    start_server()
