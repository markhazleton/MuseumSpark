#!/usr/bin/env python3
"""Thin wrapper for Phase 2 scoring implementation.

The full implementation lives in `phase2_scoring_impl.py` so this entrypoint
stays stable while the implementation remains modular.
"""

from phase2_scoring_impl import main


if __name__ == "__main__":
    raise SystemExit(main())
