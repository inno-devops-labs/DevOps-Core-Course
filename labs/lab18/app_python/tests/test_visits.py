from visits import read_visits, increment_visits


def test_read_visits_default():
    assert read_visits() == 0


def test_increment_visits():
    assert increment_visits() == 1
    assert increment_visits() == 2
    assert increment_visits() == 3


def test_read_after_increment():
    increment_visits()
    increment_visits()
    assert read_visits() == 2
