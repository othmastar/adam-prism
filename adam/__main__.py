"""Adam Prism CLI entry point — `python -m adam` or `adam`"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from main import main
main()
