"""Adam Prism CLI entry point — `python -m adam` or `adam`

[M17-M18 FIX]
- Added comment explaining why sys.path is modified (development convenience)
- Use try/except so it works both with and without the path manipulation
"""

import sys
from pathlib import Path

# [M17-M18] Add project root to sys.path for development convenience.
# This allows running `python -m adam` from the backend/ directory.
# In a proper installation (pip install), this is not needed.
_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

try:
    from main import main
except ImportError:
    # [M17-M18] If import fails (e.g., installed as package), try without path manipulation
    from adam.main import main

main()
