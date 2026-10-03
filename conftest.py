"""Pytest bootstrap: give plain test classes the unittest assert helpers.

The checked-in test classes are written against ``unittest.TestCase``
assertions but do not inherit from it.
"""


def assert_is_not_none(self, value, msg=None):
    if value is None:
        raise AssertionError(msg or f"{value!r} is None")


def assert_is_none(self, value, msg=None):
    if value is not None:
        raise AssertionError(msg or f"{value!r} is not None")


def assert_true(self, value, msg=None):
    if not value:
        raise AssertionError(msg or f"{value!r} is not truthy")


def assert_false(self, value, msg=None):
    if value:
        raise AssertionError(msg or f"{value!r} is not falsy")


def assert_equal(self, first, second, msg=None):
    if first != second:
        raise AssertionError(msg or f"{first!r} != {second!r}")


def assert_not_equal(self, first, second, msg=None):
    if first == second:
        raise AssertionError(msg or f"{first!r} == {second!r}")


def assert_in(self, member, container, msg=None):
    if member not in container:
        raise AssertionError(msg or f"{member!r} not in {container!r}")


def assert_not_in(self, member, container, msg=None):
    if member in container:
        raise AssertionError(msg or f"{member!r} in {container!r}")


def assert_almost_equal(self, first, second, places=7, msg=None, delta=None):
    if delta is not None:
        if abs(first - second) > delta:
            raise AssertionError(msg or f"{first!r} not within {delta} of {second!r}")
    elif round(abs(first - second), places) != 0:
        raise AssertionError(msg or f"{first!r} != {second!r} within {places} places")


class _AssertRaisesContext:
    def __init__(self, expected):
        self.expected = expected

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is None:
            raise AssertionError(f"{self.expected.__name__} not raised")
        return issubclass(exc_type, self.expected)


def assert_raises(self, expected, *args, **kwargs):
    if not args:
        return _AssertRaisesContext(expected)
    fn = args[0]
    try:
        fn(*args[1:], **kwargs)
    except expected:
        return
    raise AssertionError(f"{expected.__name__} not raised")


_STANDALONE_ASSERTS = {
    "assertIsNotNone": assert_is_not_none,
    "assertIsNone": assert_is_none,
    "assertTrue": assert_true,
    "assertFalse": assert_false,
    "assertEquals": assert_equal,
    "assertEqual": assert_equal,
    "assertNotEqual": assert_not_equal,
    "assertIn": assert_in,
    "assertNotIn": assert_not_in,
    "assertAlmostEqual": assert_almost_equal,
    "assertRaises": assert_raises,
}


def pytest_collection_modifyitems(items):
    for item in items:
        cls = getattr(item, "cls", None)
        if cls is None:
            continue
        for name, func in _STANDALONE_ASSERTS.items():
            if not hasattr(cls, name):
                setattr(cls, name, func)
