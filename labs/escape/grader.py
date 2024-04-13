import traceback
import os
import multiprocessing
import hashlib

def scenario_one():
    secret = os.urandom(256)

    def guess(x):
        return x == secret

    import attack
    r = attack.attack_one(guess)

    if type(r) != bytes or r != secret:
        raise Exception("did not return correct secret")

def scenario_two():
    secret = os.urandom(256)

    import attack
    r = attack.attack_two()

    if type(r) != bytes or r != secret:
        raise Exception("did not return correct secret")

def scenario_three():
    import attack
    r = attack.attack_three()

    secret = os.urandom(256)

    if type(r) != bytes or r != secret:
        raise Exception("did not return correct secret")

class SecretStore:
    def __init__(self, secret):
        self.myself = self
        self.secret = secret
        self.msg = 'the secret is %s' % list(secret)

def scenario_four():
    secret = os.urandom(256)
    store = SecretStore(secret)
    h = hashlib.sha256(secret).digest()

    secret = None
    store = None

    import attack
    r = attack.attack_four()

    if type(r) != bytes or hashlib.sha256(r).digest() != h:
        raise Exception("did not return correct secret")

checks = {
    "one": scenario_one,
    "two": scenario_two,
    "three": scenario_three,
    "four": scenario_four,
}

if __name__ == '__main__':
    for n, f in checks.items():
        try:
            p = multiprocessing.Pool(processes = 1)
            p.apply(f)
            print("%s: pass" % n)
        except:
            traceback.print_exc()
            print("%s: fail" % n)
