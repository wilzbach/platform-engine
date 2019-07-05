import math


def percentile(data: list, percent: float, sorted=False):
    """
    Calculates and returns the `percent` percentile value from `data`
    :param data: Data under consideration (list)
    :param percent: Percentile value (floating point number between 0-1)
    :param sorted: Boolean indicating whether `data` is sorted
    """
    if not sorted:
        data.sort()
    pos = (len(data) - 1) * percent
    f = math.floor(pos)
    c = math.ceil(pos)
    if f == c:
        return data[int(pos)]
    else:
        # Return weighted average
        d0 = data[int(f)] * (c - pos)
        d1 = data[int(c)] * (pos - f)
        return d0 + d1
