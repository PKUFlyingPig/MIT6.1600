import bitstring
import hashlib

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
            path = traversal_path(fake_key)
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
        proof = self._store.lookup(key)
        if proof.key is None and proof.val is None:
            node_hash = H_empty()
        else:
            node_hash = H_kv(proof.key, proof.val)

        path = traversal_path(key)
        for (leaf_direction, sibling) in reversed(list(zip(path[2:], proof.siblings[2:]))):
            children = [None, None]
            children[int(leaf_direction)] = node_hash
            children[int(not leaf_direction)] = sibling
            node_hash = H_internal(children)
        
        if path[1] == False:
            proof.key = node_hash
            proof.val = proof.siblings[1]
        else:
            proof.key = proof.siblings[1]
            proof.val = node_hash
        proof.siblings = [proof.siblings[0]]
        
        return proof

class AttackFour:
    def __init__(self, s):
        self._store = s

    def insert(self, key, val):
        return self._store.insert(key, val)

    def attack_fake_key(self):
        return b''

    def lookup(self, key):
        return self._store.lookup(key)
