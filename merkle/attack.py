import bitstring
import hashlib

def H(*args):
    return hashlib.sha256(b''.join(args)).digest()

class AttackOne:
    def __init__(self, s):
        self._store = s
        self._store.reset()
        self._store.insert(b"hellow", b"orld")

    def attack_fake_key(self):
        return b"hellow"

    def lookup(self, key):
        return self._store.lookup(key)

class AttackTwo:
    def __init__(self, s):
        self._store = s
        arr = [b'0']*5050
        self.attack_key = b'\xbf[\x81\xae\xffB\xdd\x01\xd5\x1f\xd2G\x94:`i\xc2\x13:\xeb\x84\x87\x8d\x19\x9c\xef\xa8FQ\x12\xb5\xc2'
        self.attack_val = b'\xe3e'
        self.fake_kvs = {}
        for i in range(1, 5000):
            fake_key = b''.join(arr[:i])
            fake_value = b''.join(arr[i:])
            path = bitstring.BitArray(H(fake_key))
            if path[0] == False:
                self.fake_kvs[fake_key] = fake_value

    def attack_fake_keys(self):
        return self.fake_kvs.keys()

    def attack_key_value(self):
        return self.attack_key, self.attack_val

    def lookup(self, key):
        proof = self._store.lookup(key)
        proof.key = key
        proof.val = self.fake_kvs[key]
        proof.siblings = [self.attack_val]
        return proof

class AttackThree:
    def __init__(self, s):
        self._store = s

    def lookup(self, key):
        return self._store.lookup(key)

class AttackFour:
    def __init__(self, s):
        self._store = s

    def insert(self, key, val):
        return self._store.insert(key, val)

    def attack_fake_key(self):
        return b''

    def lookup(self, key):
        return self._store.lookup(key)
