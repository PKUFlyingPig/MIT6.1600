import hashlib

def H(b):
    return hashlib.blake2b(b, digest_size=7).digest()
