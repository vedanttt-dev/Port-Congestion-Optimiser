#!/usr/bin/env python
"""Generate synthetic port scenario data.

Usage (from ``backend/``)::

    python ../scripts/generate_data.py --seed 42 --weeks 4 --output ../data/raw

Or run via ``python -m`` from the repo root::

    python scripts/generate_data.py --seed 42 --weeks 4
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure backend/ is on sys.path so ``app.*`` imports work.
_HERE = Path(__file__).resolve().parent
_BACKEND = _HERE.parent / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.data.generator import generate_scenario, save_scenario


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic container terminal scenario data.",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducibility (default: 42).",
    )
    parser.add_argument(
        "--weeks", type=int, default=4,
        help="Weeks of vessel arrivals to generate (default: 4).",
    )
    parser.add_argument(
        "--as-of", type=float, default=0.0,
        help="Simulation-hour clock offset (default: 0).",
    )
    parser.add_argument(
        "--output", type=str, default="data/raw",
        help="Output directory for JSON files (default: data/raw).",
    )
    args = parser.parse_args()

    print(f"Generating scenario: seed={args.seed}, weeks={args.weeks} ...")
    scenario = generate_scenario(
        seed=args.seed, weeks=args.weeks, as_of_h=args.as_of,
    )

    meta = scenario["meta"]
    print(f"  Vessels  : {meta['total_arrivals']} ({meta['arrivals_per_week']}/week)")
    print(f"  Berths   : {meta['num_berths']}")
    print(f"  Cranes   : {meta['num_cranes']}")
    print(f"  Yard     : {meta['yard_current_teu']:,}/{meta['yard_teu_capacity']:,} TEU ({meta['yard_util_pct']}%)")
    print(f"  Alt ports: {meta['num_alt_ports']}")

    saved = save_scenario(scenario, args.output)
    print(f"\nSaved to {args.output}/:")
    for name, path in saved.items():
        print(f"  {name:12s} -> {path}")


if __name__ == "__main__":
    main()
