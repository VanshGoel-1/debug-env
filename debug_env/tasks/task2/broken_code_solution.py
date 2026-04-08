def is_even(n):
    return n % 2 == 0


def get_evens(numbers):
    return [n for n in numbers if is_even(n)]


def sum_of_evens(numbers):
    return sum(get_evens(numbers))
