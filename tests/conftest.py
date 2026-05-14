"""pytest configuration: ensure project root and tests/ are importable."""
from __future__ import annotations

import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent

for p in (str(PROJECT_ROOT), str(TESTS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)
