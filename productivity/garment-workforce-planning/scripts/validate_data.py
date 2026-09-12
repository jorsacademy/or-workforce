from __future__ import annotations

import sys
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parents[1]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from src.data import REQUIRED_COLUMNS, load_workforce_data


def main() -> None:
    cfg = yaml.safe_load((PROJECT / "config.yaml").read_text())
    path = PROJECT / cfg["data"]["path"]
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Run: python scripts/download_data.py")

    df = load_workforce_data(path)
    expected_rows = int(cfg["data"].get("expected_rows", 1197))
    checks = {
        "rows": len(df),
        "columns": len(df.columns),
        "dates": int(df["date"].nunique()),
        "teams": int(df["team"].nunique()),
        "missing_wip": int(df["wip"].isna().sum()),
        "target_min": float(df["actual_productivity"].min()),
        "target_max": float(df["actual_productivity"].max()),
    }
    print(checks)

    assert len(df) == expected_rows
    assert REQUIRED_COLUMNS.issubset(df.columns)
    assert df["date"].notna().all()
    assert df["actual_productivity"].notna().all()
    assert df["actual_productivity"].between(0, 1.5).all()


if __name__ == "__main__":
    main()
