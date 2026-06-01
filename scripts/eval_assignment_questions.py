#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.evals.assignment_eval import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
