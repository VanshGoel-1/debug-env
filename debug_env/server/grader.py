def grade(pass_rate: float) -> float:
    """Baseline reward — direct pass rate (used as fallback)."""
    return float(pass_rate)


def grade_by_comparison(submitted: str, reference: str) -> float:
    """
    Compare submitted code to reference line-by-line.
    +10 for each matching line, -10 for each non-matching line.
    Normalized to [0, 1] via (score + n*10) / (2*n*10).
    """
    sub_lines = submitted.splitlines()
    ref_lines = reference.splitlines()
    n = max(len(sub_lines), len(ref_lines))
    if n == 0:
        return 0.0

    score = 0
    for i in range(n):
        sub_line = sub_lines[i] if i < len(sub_lines) else ""
        ref_line = ref_lines[i] if i < len(ref_lines) else ""
        score += 10 if sub_line == ref_line else -10

    normalized = (score + n * 10) / (2 * n * 10)
    return round(max(0.0, min(1.0, normalized)), 4)


def grade_with_steps(pass_rate: float, step_count: int, max_steps: int = 40) -> float:
    """
    Shaped reward that incentivises efficiency.

    - Partial credit: linear pass_rate contribution
    - Step penalty: -0.01 per step after the first 3 (discourages thrashing), capped at -0.3
    - Completion bonus: +0.1 flat for reaching pass_rate == 1.0
    - Efficiency bonus: up to +0.2 for solving early (only on full solve)
    """
    if pass_rate == 0.0:
        return 0.0

    base = float(pass_rate)

    # Step penalty: starts after step 3, max -0.3
    penalty = min(max(0.0, (step_count - 3) * 0.01), 0.3)

    # Completion bonus
    completion_bonus = 0.1 if pass_rate == 1.0 else 0.0

    # Efficiency bonus: only on full solve, scales with how early
    efficiency_bonus = 0.0
    if pass_rate == 1.0 and max_steps > 0:
        efficiency_bonus = 0.2 * max(0.0, 1.0 - step_count / max_steps)

    reward = base - penalty + completion_bonus + efficiency_bonus
    return round(min(max(reward, 0.0), 1.0), 4)
