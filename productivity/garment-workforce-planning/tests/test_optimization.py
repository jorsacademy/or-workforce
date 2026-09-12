import numpy as np

from src.optimization import solve_reallocation


def test_milp_preserves_headcount_and_budget():
    current = np.array([10, 10, 10])
    solution = solve_reallocation(
        current_workers=current,
        worker_gain=np.array([0.03, 0.01, -0.01]),
        overtime_block_gain=np.array([0.02, 0.01, 0.00]),
        baseline_productivity=np.array([0.7, 0.7, 0.7]),
        total_workers=30,
        worker_flex=2,
        overtime_budget_blocks=4,
        max_overtime_blocks_per_team=3,
        overtime_penalty=0.001,
    )
    assert int(solution["optimized_workers"].sum()) == 30
    assert int(solution["overtime_blocks"].sum()) <= 4
    assert solution.loc[0, "optimized_workers"] >= solution.loc[2, "optimized_workers"]
