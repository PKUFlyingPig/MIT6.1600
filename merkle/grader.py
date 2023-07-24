import store
import attack
import client
import traceback

def attack_one():
    s = store.Store()
    c = client.Client(s)

    k = b'hello'
    v = b'world'
    c.insert(k, v)

    a = attack.AttackOne(s)
    c._store = a
    ak = a.attack_fake_key()

    r = c.lookup(ak)

    if type(ak) != bytes or ak == k:
        raise Exception("attack key must be different from k")

    if r is None:
        raise Exception("attack lookup returns None")

def attack_two():
    s = store.Store()
    c = client.Client(s)

    a = attack.AttackTwo(s)
    keys = a.attack_fake_keys()
    k, v = a.attack_key_value()

    if not all([type(k) == bytes for k in keys]):
        raise Exception("fake keys must all be bytes")
    if len(set(keys)) < 1000:
        raise Exception("less than 1000 fake keys")
    if len(k) + len(v) > 100:
        raise Exception("chosen key/value too long")

    c.insert(k, v)
    c._store = a
    for k in keys:
        r = c.lookup(k)
        if r is None:
            raise Exception("fake key %s not found" % k)

def attack_three():
    s = store.Store()
    a = attack.AttackThree(s)
    c = client.Client(a)

    for i in range(1000):
        k = b'k%d' % i
        v = b'v%d' % i
        c.insert(k, v)

    ak = a.attack_fake_key()
    if type(ak) != bytes:
        raise Exception("fake key must be bytes")

    av = c.lookup(ak)
    if av is None:
        raise Exception("fake key not present")
    if len(ak) + len(av) < 1000:
        raise Exception("fake key and value not long enough")

checks = {
    "one": attack_one,
    "two": attack_two,
    "three": attack_three,
}

if __name__ == '__main__':
    for n, f in checks.items():
        try:
            f()
            print("%s: pass" % n)
        except:
            traceback.print_exc()
            print("%s: fail" % n)
