import typing as t


def flatten(o):
    """
    Return all of the integers, strings, and bytes in an object
    in a flattened list.

    >>> a = [5, "foo", b"xyz", {'hello': 'world'}, [42, 55], []]
    >>> flatten(a)
    [5, 'foo', b'xyz', 'world', 42, 55]
    """
    if type(o) in (int, str, bytes):
        return [o]
    if type(o) is list:
        return sum([flatten(i) for i in o], [])
    if type(o) is dict:
        return sum([flatten(v) for k, v in sorted(o.items())], [])
    raise Exception("cannot flatten type %s" % type(o))


def replace_val(
    o: t.Union[int, str, bytes, list, dict],
    a: t.Union[int, str, bytes],
    b: t.Union[int, str, bytes],
):
    """
    Replace occurrences of a with b inside o.  The type of a (and b)
    should be one of int, str, or bytes.

    >>> x = [1, 2, 3, {"hello": "world", "foo": 2, "bar": [5, 2, 2, 1]}]
    >>> replace_val(x, 2, 99)
    [1, 99, 3, {'bar': [5, 99, 99, 1], 'foo': 99, 'hello': 'world'}]
    """
    if type(o) in (int, str, bytes):
        if o == a:
            return b
        return o
    if type(o) is list:
        return [replace_val(e, a, b) for e in o]
    if type(o) is dict:
        d = {}
        for k, v in sorted(o.items()):
            d[k] = replace_val(v, a, b)
        return d
    raise Exception("cannot replace_val type %s" % type(o))

