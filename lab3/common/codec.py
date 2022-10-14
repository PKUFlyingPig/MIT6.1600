#!/usr/bin/env python3

"""
A simple codec for encoding data structures as bytes.
The supported data structures are integers, strings, bytes,
dictionaries, and lists.
"""

import msgpack
import collections
import typing as t

import common.errors as errors


def canonicalize(o):
    """Return a version of o that will produce a canonical encoding."""
    if type(o) in (int, str, bytes):
        return o
    if type(o) is list:
        return [canonicalize(e) for e in o]
    if type(o) is dict:
        d = collections.OrderedDict()
        for k, v in sorted(o.items()):
            d[canonicalize(k)] = canonicalize(v)
        return d
    raise Exception("cannot canonicalize type %s" % type(o))


def encode(o: t.Union[int, str, bytes, list, dict]) -> bytes:
    """
    Encode the given object into a byte array. Acceptable object
    types are `int`, `str`, `bytes`, `list` and `dict` (but these
    may be nested).

    >>> a = {"foo": 5, "bar": 7}
    >>> b = {"bar": 7, "foo": 5}
    >>> encode(a).hex()
    '82a362617207a3666f6f05'
    >>> encode(b).hex()
    '82a362617207a3666f6f05'
    >>> c = {"foo": 5, "bar": 7, "baz": [5, 9, "hello", 1]}
    >>> encode(c).hex()
    '83a362617207a362617a940509a568656c6c6f01a3666f6f05'
    >>> decode(encode(c))
    {'bar': 7, 'baz': [5, 9, 'hello', 1], 'foo': 5}
    >>> encode(decode(encode(c))).hex()
    '83a362617207a362617a940509a568656c6c6f01a3666f6f05'
    """
    return msgpack.packb(canonicalize(o))


def decode(d) -> t.Any:
    """
    Decode the given byte array, produced by `encode()`, into the original
    object.

    >>> a = {"foo": 5, "bar": 7}
    >>> b = {"bar": 7, "foo": 5}
    >>> encode(a).hex()
    '82a362617207a3666f6f05'
    >>> encode(b).hex()
    '82a362617207a3666f6f05'
    >>> c = {"foo": 5, "bar": 7, "baz": [5, 9, "hello", 1]}
    >>> encode(c).hex()
    '83a362617207a362617a940509a568656c6c6f01a3666f6f05'
    >>> decode(encode(c))
    {'bar': 7, 'baz': [5, 9, 'hello', 1], 'foo': 5}
    >>> encode(decode(encode(c))).hex()
    '83a362617207a362617a940509a568656c6c6f01a3666f6f05'
    """
    try:
        return msgpack.unpackb(d)
    except:
        raise errors.MalformedEncodingError(d)

