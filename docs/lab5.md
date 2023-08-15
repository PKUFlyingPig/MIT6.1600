---
title: "Lab 5: Fuzzing"
---

<style type="text/css">
    ol { list-style-type: upper-alpha; }
</style>

In this lab assignment, you will use fuzzing
to find bugs and make code more robust.  The
starter code that you will be working with is available at
[https://github.com/mit-pdos/6.1600-labs/tree/main/fuzz](https://github.com/mit-pdos/6.1600-labs/tree/main/fuzz),
and you will also be using the [Atheris fuzzer for Python](https://github.com/google/atheris).

# Finding bugs

We have written a buggy library that implements the
[MessagePack](https://github.com/msgpack/msgpack/blob/master/spec.md)
encoding format.  MessagePack is similar to JSON, in that it allows
encoding basic data types (integers, booleans, dictionaries, lists/tuples,
etc), and does not require a pre-defined schema for the data that you
want to encode.  Our buggy library is available as
[`msgpacker.py`](https://github.com/mit-pdos/6.1600-labs/blob/main/fuzz/msgpacker.py)
in the starter code repo.  You can see how to use this library in
[`msgpacker_example.py`](https://github.com/mit-pdos/6.1600-labs/blob/main/fuzz/msgpacker_example.py):

```
    % python msgpacker_example.py
    example: {'Hello': 'world', 'foo': ('bar', 'baz', 'quux'), 'flag': True, 'count': 123}
    encoding: b'\x84\xa5Hello\xa5world\xa3foo\x93\xa3bar\xa3baz\xa4quux\xa4flag\xc2\xa5count{'
    example2: {'Hello': 'world', 'foo': ('bar', 'baz', 'quux'), 'flag': True, 'count': 123}
    % 
```

What you can see is that we constructed the `example` data structure,
which is a dictionary containing lists/tuples, booleans, strings,
and integers.  The second line is the MessagePack encoding of that value,
and the last line shows `example2`, the decoding of the encoding; it is
identical to the `example` data structure that what we started with.

Your job is to find and fix bugs in this library.  We will test it
against our own test cases, but we will not hand out these test cases
to you upfront.  Instead, your job is to gain confidence that your
fixed library is correct before you submit it for grading.

We think that fuzzing is likely to be a productive way of
finding bugs in the `msgpacker.py` library.  You can use the
[Atheris fuzzer](https://github.com/google/atheris).  To set
up an environment containing this fuzzer library, you can run `make`,
which sets up a corresponding virtualenv:

```
    % make
    python3 -m venv venv
    venv/bin/pip install -r requirements.txt || ( rm -r venv; false )
    Collecting atheris
      Using cached atheris-2.2.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (31.4 MB)
    Collecting msgpack
      Using cached msgpack-1.0.5-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (325 kB)
    Installing collected packages: msgpack, atheris
    Successfully installed atheris-2.2.2 msgpack-1.0.5
    touch venv
    % ./venv/bin/python ...
```

We also installed the standard msgpack library for Python, which you
can use as needed in your fuzzing process.


# Building a codec

Your job for the second part of the lab is to build a codec for bytestrings.
That is, you will implement a pair of functions, `encode()` and `decode()`,
that will take bytestrings (`bytes` in Python) as input, and produce bytestrings
as output.  The reason you're building a custom codec is that we would like to
encode strings in a specific way:

- Your codec must encode bytes into bytes, and decode back into bytes.

- Your codec must be able to encode arbitrary bytes.  It must be possible
  to encode any byte sequence, and then decode it correctly (i.e.,
  get back the original input).

- The encoding must be printable.  That is, regardless of what bytes your
  `encode()` function is asked to encode, the result must be a sequence
  of bytes that are all printable---so that you can, say, print it on
  a piece of paper and give it to someone, or print it on a billboard,
  etc.  Specifically, by _printable_ we mean the bytes in Python's
  `string.printable[:94]` (i.e., excluding whitespace).
  Your encodings cannot contain non-printable bytes.

- Alphanumeric inputs (where every character is in `string.ascii_letters`
  or `string.digits`) must be encoded one-to-one: the encoding must be the
  same as the input.  This ensures that messages that are already printable,
  like "Apples", are encoded as-is to "Apples".

- The encoding should not be too long, even if there are arbitrary input bytes.
  Specifically, the encoding can be at most 3x the size of the input, in the worst case.

- The encoding must be recoverable.  This means that, if you take an encoding
  and chop off some parts of it (at the beginning or at the end), then decoding
  that chopped part should produce the corresponding part of the original string,
  modulo things that might have gotten cut off at each end.

Your job is to implement this codec.  We have
provided a skeleton file for you to get started,
[`codec.py`](https://github.com/mit-pdos/6.1600-labs/blob/main/fuzz/codec.py).
We do not supply any test cases for you to use; feel free to use any
tools available at your disposal, such as the Atheris fuzzer, to gain
confidence that your codec is correct.  We will grade it with our own
test cases when you submit your solution.
