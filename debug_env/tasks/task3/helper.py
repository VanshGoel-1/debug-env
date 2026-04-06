def clamp(value, min_val, max_val):
    if value < min_val:
        return max_val  # Bug: should return min_val
    if value > max_val:
        return min_val  # Bug: should return max_val
    return value
