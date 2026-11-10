from pathlib import Path
import sys

# Make the repository's top-level risk_kit.py importable during pytest collection.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
