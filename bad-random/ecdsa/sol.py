import hashlib
from ecdsa import SigningKey, NIST256p
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
    pass