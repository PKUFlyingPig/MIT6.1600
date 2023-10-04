
from sol import problem_1a, problem_3b
from ecdsa import SigningKey, NIST256p
from ecdsa.util import sigencode_string, sigdecode_string
import hashlib 
import keygen
import time


import traceback

def test_1():
    b = b'%d' % time.time()

    date_string = time.strftime("%Y-%m-%d")
    h = hashlib.sha256(b).digest()
    # Convert digest byte-array to an integer, use as secret key
    secexp = int.from_bytes(h, "big")
    sk = SigningKey.from_secret_exponent(secexp, curve=NIST256p)
    vk = sk.verifying_key
    str(vk.to_pem(), "ascii")


    result = problem_1a(date_string,vk)
    if(result != sk):
        raise Exception(f"{result} does not equal signing key.")




def test_2():
    message_1 = str("message_1")
    message_2 = str("message_2")

    sk = SigningKey.generate()
    pk = sk.privkey.secret_multiplier

    vk = sk.get_verifying_key()

    sig = sk.sign(message_1.encode('utf-8'),k=19)
    r1, s1 = sigdecode_string(sig, vk.pubkey.order)
    
    sig2 = sk.sign(message_2.encode("utf-8"),k=19)
    r2, s2 = sigdecode_string(sig2, vk.pubkey.order)

    Hm1 = hashlib.sha1(message_1.encode('utf-8')).hexdigest()
    Hm2 = hashlib.sha1(message_2.encode('utf-8')).hexdigest()

    Hm1 = int(Hm1, 16)
    Hm2 = int(Hm2, 16)

    #Start the attack
    result = problem_2b((r1,s1), (r2,s2), Hm1, Hm2)
    
    if(result != pk):
        raise Exception("Attack key does not equal private key.")
   

checks = {
    "1": test_1,
    "2": test_2,
}

if __name__ == '__main__':
    for n, f in checks.items():
        try:
            f()
            print("%s: pass" % n)
        except:
            traceback.print_exc()
            print("%s: fail" % n)