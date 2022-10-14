import traceback
import typing as t
import types

# contains tuples of the test function itself, the maximum amount of
# points for that test, and the expected number of points in starter code
tests: t.Dict[str, t.Tuple[t.Callable[[], int], int, int]] = {}


def test_case(points: int = 1, starter_points: int = 0):
    """
    Decorator to add to a test case that adds it to the
    set of test cases to run.

    Test case will be added when the containing module
    is imported (and the decorator is executed)
    """

    def wrapped_test(f: t.Callable[[], int]):
        tests[f.__name__] = (f, points, starter_points)
        return f

    return wrapped_test


def scale_test(test: t.Callable[[], int], factor: float) -> t.Callable[[], int]:
    """
    Wraps the given test to scale (multiply) its output points by the given factor.

    Updates the related entry in the list of tests. Expects the test to
    already be in the tests directory (ie this is applied after @test_case)
    """

    def wrapped_test(f: t.Callable):
        scaled_test = lambda: f() * factor
        points = tests[f.__name__][1]
        starter_points = tests[f.__name__][2]
        tests[f.__name__] = (scaled_test, points * factor, starter_points * factor)
        return scaled_test

    return wrapped_test


def scale_all_tests_in_module(m: types.ModuleType, factor: float) -> None:
    """
    Scale all tests in the given module by the given factor.
    """
    for k, v in vars(m).items():
        if isinstance(v, types.FunctionType) and v.__name__ in tests:
            # Note: we round the points here and the max points below to avoid floating point nastiness
            scaled_test = lambda f=v: round(
                f() * factor, 5
            )  # binding value: https://stackoverflow.com/questions/19837486/lambda-in-a-loop
            scaled_test.__name__ = (
                v.__name__
            )  # avoid the function just being called "<lambda>"
            vars(m)[k] = scaled_test
            points = tests[v.__name__][1]
            starter_points = tests[v.__name__][2]
            tests[v.__name__] = (scaled_test, round(points * factor, 5), round(starter_points * factor, 5))


def run_tests():
    # TODO add timeouts to tests (to handle infinite loops)

    total_pts = 0
    max_score = 0
    starter_pts = 0
    results = []
    for test_name, (test_case, test_points, starter_points) in tests.items():
        max_score += test_points
        try:
            points = test_case()
        except Exception as e:
            traceback.print_exc()
            points = 0
        print(f"{test_case.__name__}: {points}/{test_points} point(s)")
        total_pts += points
        starter_pts += starter_points
        results.append(
            {
                "name": test_name,
                "max_score": test_points,
                "starter_score": starter_points,
                "score": points,
            }
        )

    print("----------------------------------------------------------------")
    print("total: {} / {} pts".format(round(total_pts, 3), round(max_score, 3)))
    return {
        "max_score": max_score,
        "starter_score": starter_pts,
        "score": total_pts,
        "tests": results,
    }

