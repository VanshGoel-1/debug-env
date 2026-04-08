import ast
import difflib

def _clamp(val: float) -> float:
    return float(round(min(max(val, 0.0001), 0.9999), 4))

def grade(pass_rate: float) -> float:
    """Baseline reward — direct pass rate (used as fallback)."""
    return _clamp(pass_rate)


def grade_by_comparison(submitted: str, reference: str) -> float:
    """
    Grades submitted code against reference code, prioritizing semantic exactness.
    - First attempts AST parsing: if both codes produce identical ASTs, returns 1.0.
    - If AST parsing fails or differs, falls back to difflib SequenceMatcher on sanitized lines.
    """
    try:
        sub_ast = ast.unparse(ast.parse(submitted))
        ref_ast = ast.unparse(ast.parse(reference))
        if sub_ast == ref_ast:
            return 0.9999
    except Exception:
        pass  # Fall back to token comparison if syntax is invalid

    sub_lines = [line.strip() for line in submitted.splitlines() if line.strip()]
    ref_lines = [line.strip() for line in reference.splitlines() if line.strip()]
    
    if not ref_lines:
        return 0.0001 if sub_lines else 0.9999
        
    matcher = difflib.SequenceMatcher(None, sub_lines, ref_lines)
    return _clamp(matcher.ratio())


def grade_with_steps(pass_rate: float, step_count: int, max_steps: int = 40) -> float:
    """
    Shaped reward that incentivises efficiency.

    - Partial credit: linear pass_rate contribution
    - Step penalty: -0.01 per step after the first 3 (discourages thrashing), capped at -0.3
    - Completion bonus: +0.1 flat for reaching pass_rate == 1.0
    - Efficiency bonus: up to +0.2 for solving early (only on full solve)
    """
    if pass_rate == 0.0:
        return 0.0001

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
    return _clamp(reward)
