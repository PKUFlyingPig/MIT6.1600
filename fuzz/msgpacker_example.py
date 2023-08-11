import msgpacker

example = {
    "Hello": "world",
    "foo": ("bar", "baz", "quux"),
    "flag": True,
    "count": 123,
}

print("example:", example)

enc = msgpacker.encoder()
enc.encode(example)
res = enc.get_buf()

print("encoding:", res)

dec = msgpacker.decoder(res)
example2 = dec.decode()

print("example2:", example2)
