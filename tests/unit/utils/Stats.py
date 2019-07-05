from asyncy.utils import Stats


def test_percentile():
    data = [5, 4, 1, 2, 3]
    res = Stats.percentile(data, 0.5)
    assert res == 3
