"""Pytest config for backend tests - adds backend/ to sys.path"""
import sys
from pathlib import Path

_backend = Path(__file__).parent.parent / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))
