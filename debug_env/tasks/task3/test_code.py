from broken_code import normalize_grade, letter_grade, class_average


def test_normalize_grade():
    assert normalize_grade(85) == 85
    assert normalize_grade(-10) == 0
    assert normalize_grade(110) == 100


def test_letter_grade():
    assert letter_grade(95) == 'A'
    assert letter_grade(85) == 'B'
    assert letter_grade(75) == 'C'
    assert letter_grade(65) == 'D'
    assert letter_grade(50) == 'F'


def test_class_average():
    assert class_average([80, 90, 70]) == 80.0
    assert class_average([]) == 0.0
    assert class_average([100]) == 100.0
