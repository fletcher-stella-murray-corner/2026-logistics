#!/usr/bin/env python3
"""Rebuild every feature's public page(s) in one call.

Run this after hand-editing any data file (shared/data/people.json,
shared/data/structures.json, shared/data/vehicles.json,
timeline/data/travel.json, timeline/data/meals.json,
timeline/data/activities.json) or any page template. See technical.md ->
Scripts.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # repo root


def main():
    if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    subprocess.run([sys.executable, str(ROOT / "timeline" / "scripts" / "build.py")], check=True)
    subprocess.run([sys.executable, str(ROOT / "family-tree" / "scripts" / "build.py")], check=True)


if __name__ == "__main__":
    main()
