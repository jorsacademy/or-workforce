from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp

from .modeling import feature_matrix


def estimate_marginal_gains(
    model,
    case: pd.DataFrame,
    worker_step: int = 1,
    overtime_block_minutes: int = 60,
) -> pd.DataFrame:
    base = model.predict(feature_matrix(case))

    worker_case = case.copy()
    worker_case["no_of_workers"] = worker_case["no_of_workers"].astype(float) + worker_step
    worker_pred = model.predict(feature_matrix(worker_case))

    overtime_case = case.copy()
    overtime_case["over_time"] = overtime_case["over_time"].astype(float) + overtime_block_minutes
    overtime_pred = model.predict(feature_matrix(overtime_case))

    out = pd.DataFrame(index=case.index)
    out["baseline_productivity"] = base
    out["worker_gain"] = (worker_pred - base) / float(worker_step)
    out["overtime_block_gain"] = overtime_pred - base
    return out


def solve_reallocation(
    current_workers: np.ndarray,
    worker_gain: np.ndarray,
    overtime_block_gain: np.ndarray,
    baseline_productivity: np.ndarray,
    *,
    total_workers: int | None = None,
    worker_flex: int = 3,
    overtime_budget_blocks: int = 80,
    max_overtime_blocks_per_team: int = 20,
    overtime_penalty: float = 0.001,
) -> pd.DataFrame:
    current = np.rint(np.asarray(current_workers, dtype=float)).astype(int)
    wg = np.asarray(worker_gain, dtype=float)
    og = np.asarray(overtime_block_gain, dtype=float)
    base = np.asarray(baseline_productivity, dtype=float)
    n = len(current)
    if not (len(wg) == len(og) == len(base) == n):
        raise ValueError("All vectors must have equal length")
    if n == 0:
        raise ValueError("No teams supplied")

    if total_workers is None:
        total_workers = int(current.sum())

    worker_lb = np.maximum(1, current - int(worker_flex))
    worker_ub = current + int(worker_flex)
    if total_workers < int(worker_lb.sum()) or total_workers > int(worker_ub.sum()):
        raise ValueError("Total headcount is incompatible with staffing bounds")

    # scipy.optimize.milp minimizes c @ x. Variables are [workers..., overtime_blocks...].
    c = np.concatenate([-wg, -(og - float(overtime_penalty))])
    integrality = np.ones(2 * n, dtype=int)
    lb = np.concatenate([worker_lb, np.zeros(n)])
    ub = np.concatenate([worker_ub, np.full(n, int(max_overtime_blocks_per_team))])

    A = np.zeros((2, 2 * n), dtype=float)
    A[0, :n] = 1.0
    A[1, n:] = 1.0
    constraints = LinearConstraint(
        A,
        lb=np.array([total_workers, 0.0]),
        ub=np.array([total_workers, float(overtime_budget_blocks)]),
    )

    result = milp(c=c, integrality=integrality, bounds=Bounds(lb, ub), constraints=constraints)
    if not result.success or result.x is None:
        raise RuntimeError(f"MILP failed: {result.message}")

    workers = np.rint(result.x[:n]).astype(int)
    overtime_blocks = np.rint(result.x[n:]).astype(int)
    estimated = base + wg * (workers - current) + og * overtime_blocks

    return pd.DataFrame(
        {
            "current_workers": current,
            "optimized_workers": workers,
            "worker_change": workers - current,
            "overtime_blocks": overtime_blocks,
            "baseline_productivity": base,
            "worker_gain": wg,
            "overtime_block_gain": og,
            "estimated_productivity": np.clip(estimated, 0.0, 1.5),
        }
    )
