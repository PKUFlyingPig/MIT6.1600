import hashlib
import bitstring

def H(*args):
    return hashlib.sha256(b''.join(args)).digest()

def H_empty():
    return b''

def H_kv(key, val):
    return H(key, val)

def H_internal(children):
    return H(children[0], children[1])

def traversal_path(key):
    return bitstring.BitArray(H(key))

class Proof:
    def __init__(self, key, val, siblings):
        self.key = key
        self.val = val
        self.siblings = siblings


