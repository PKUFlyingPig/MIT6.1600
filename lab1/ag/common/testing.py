import typing as t

# contains tuples of the test function itself and the maximum amount of
# points for that test
tests: t.Tuple[t.Callable[[], int], int] = []


def test_case(points: int = 1):
    """
    Decorator to add to a test case that adds it to the
    set of test cases to run.

    Test case will be added when the containing module
    is imported (and the decorator is executed)
    """

    def wrapped_test(f: t.Callable[[], int]):
        tests.append((f, points))
        return f

    return wrapped_test


def run_tests():
    # TODO add timeouts to tests (to handle infinite loops)

    total_pts = 0
    for test_case, test_points in tests:
        points = test_case()
        print(f"{test_case.__name__}: {points}/{test_points} point(s)")
        total_pts += points

    max_score = sum([p for _, p in tests])

    print("----------------------------------------------------------------")
    print("total: {} / {} pts".format(total_pts, max_score))

