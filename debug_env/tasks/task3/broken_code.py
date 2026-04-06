from helper import clamp


def normalize_grade(score):
    """Clamp score to valid 0-100 range."""
    return clamp(score, 0, 100)


def letter_grade(score):
    """Convert numeric score to letter grade."""
    score = normalize_grade(score)
    if score >= 90:
        return 'A'
    elif score >= 80:
        return 'B'
    elif score >= 70:
        return 'C'
    elif score >= 60:
        return 'D'
    else:
        return 'F'


def class_average(scores):
    if not scores:
        return 0.0
    return sum(scores) / len(scores)
