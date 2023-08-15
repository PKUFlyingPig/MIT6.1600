from arc4 import ARC4

import os
import zlib

class Victim:
    def __init__(self):
        self.secret = os.urandom(16)

    def crc32(self, msg):
        return zlib.crc32(msg).to_bytes(4, 'big')

    def send_packet(self, msg):
        iv = os.urandom(3)
        crc = self.crc32(msg)

        arc4 = ARC4(self.secret)
        return iv + arc4.encrypt(msg + crc)

    def receive_packet(self, ct_in):
        iv = ct_in[0:3]    # First three bytes are IV
        
        ct = ct_in[3:]
        arc4 = ARC4(self.secret)
        payload = arc4.decrypt(ct)

        msg = payload[:-4]
        crc = payload[-4:]     # Last four bytes are CRC32

        # Return msg if crc32 check succeeds.
        # Otherwise return None.
        if crc == self.crc32(msg):
            return msg
        else:
            return None

