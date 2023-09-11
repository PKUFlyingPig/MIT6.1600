class AttackOne:
    def __init__(self, s):
        self._store = s

    def attack_fake_key(self):
        return b"hello"

    def lookup(self, key):
        return self._store.lookup(key)

class AttackTwo:
    def __init__(self, s):
        self._store = s

    def attack_fake_keys(self):
        return {}

    def attack_key_value(self):
        return b"hello", b"world"

    def lookup(self, key):
        return self._store.lookup(key)

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
