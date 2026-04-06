from broken_code import is_even, get_evens, sum_of_evens


def test_is_even():
    assert is_even(2) == True
    assert is_even(3) == False
    assert is_even(0) == True
    assert is_even(7) == False


def test_get_evens():
    assert get_evens([1, 2, 3, 4]) == [2, 4]
    assert get_evens([1, 3, 5]) == []
    assert get_evens([2, 4, 6]) == [2, 4, 6]


def test_sum_of_evens():
    assert sum_of_evens([1, 2, 3, 4, 5, 6]) == 12
    assert sum_of_evens([1, 3, 5]) == 0
    assert sum_of_evens([]) == 0
