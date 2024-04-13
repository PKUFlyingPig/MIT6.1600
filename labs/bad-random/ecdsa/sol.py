import hashlib
from ecdsa import SigningKey, NIST256p, NIST192p, numbertheory
from datetime import datetime, timedelta

# Function to convert date string to the start and end timestamps for that date
def date_string_to_timestamp_range(date_str):
    start_dt = datetime.strptime(date_str, '%Y-%m-%d')
    end_dt = start_dt + timedelta(days=1)
    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp()) - 1
    return start_ts, end_ts

def check_keygen(timestamp, public_key):
    # Your logic here
    b = b'%d' % timestamp
    h = hashlib.sha256(b).digest()

    # Convert digest byte-array to an integer, use as secret key
    secexp = int.from_bytes(h, "big")

    sk = SigningKey.from_secret_exponent(secexp, curve=NIST256p)
    vk = sk.verifying_key
    return vk == public_key, sk

def problem_1a(date_string, public_key):
    start_ts, end_ts = date_string_to_timestamp_range(date_string)
    for ts in range(start_ts, end_ts + 1):
        success, sk = check_keygen(ts, public_key)
        if success:
            return sk


def problem_2b(sig1, sig2, Hm1, Hm2):
    order = NIST192p.order
    # Extract r and s from signatures
    r1, s1 = sig1
    r2, s2 = sig2

    if r1 != r2:
        raise Exception("The r values are not the same; the same nonce might not have been used.")
    
    r = r1  # r is the same in both signatures because the same nonce was used

    # Calculate k using s1, s2, Hm1, and Hm2
    # alpha_t = (s1 - s2)^-1 * (Hm1 - Hm2) (mod order)
    alpha_t = numbertheory.inverse_mod(s1 - s2, order) * (Hm1 - Hm2) % order

    # Recover secret key using one of the signatures
    # secret_key = (s1 * k - Hm1) * r^-1 (mod order)
    secret_key = (s1 * alpha_t - Hm1) * numbertheory.inverse_mod(r, order) % order
    
    return secret_key