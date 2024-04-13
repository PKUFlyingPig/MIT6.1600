
import time
from ecdsa import NIST256p, SigningKey
import hashlib

def main():
    b = b'%d' % time.time()
    h = hashlib.sha256(b).digest()

    # Convert digest byte-array to an integer, use as secret key
    secexp = int.from_bytes(h, "big")

    sk = SigningKey.from_secret_exponent(secexp, curve=NIST256p)
    vk = sk.verifying_key
    print(str(vk.to_pem(), "ascii"))

if __name__ == "__main__":
    main()
