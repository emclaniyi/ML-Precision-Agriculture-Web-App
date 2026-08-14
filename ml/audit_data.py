"""Audit a crop-training CSV before it is used for model training."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


EXPECTED_TARGET = "crop_type"
EXPECTED_SOIL = "Soil_type"


def audit(path: Path) -> None:
    frame = pd.read_csv(path)

    print(f"file: {path}")
    print(f"rows: {len(frame)}")
    print(f"columns: {', '.join(frame.columns)}")
    print(f"duplicate_rows: {int(frame.duplicated().sum())}")

    print("\nmissing_values:")
    print(frame.isna().sum().to_string())

    if EXPECTED_TARGET in frame:
        print("\nclass_counts:")
        print(frame[EXPECTED_TARGET].value_counts(dropna=False).to_string())

    if EXPECTED_TARGET in frame and EXPECTED_SOIL in frame:
        print("\nclass_by_soil_type:")
        print(pd.crosstab(frame[EXPECTED_TARGET], frame[EXPECTED_SOIL]).to_string())

    numeric = frame.select_dtypes(include="number")
    if not numeric.empty:
        print("\nnumeric_ranges:")
        print(numeric.agg(["min", "max"]).T.to_string())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "final_data.csv",
        help="CSV file to audit (defaults to data/final_data.csv)",
    )
    args = parser.parse_args()
    audit(args.path)


if __name__ == "__main__":
    main()
