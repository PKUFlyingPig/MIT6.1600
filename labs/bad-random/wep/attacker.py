import zlib

class Attacker:
    def __init__(self, v):
        self.victim = v

    def crc32(self, msg):
        return zlib.crc32(msg).to_bytes(4, 'big')

    def attack_one(self, plaintext, ciphertext, attack_msg):
        # You may NOT use self.victim, since this is
        # a passive attack.

        ### Your cleverness here

        crc = self.crc32(plaintext)
        pay_load = plaintext + crc
        iv = ciphertext[0:3]
        encoded = ciphertext[3:]
        assert len(encoded) == 260 and len(pay_load) == 260
        key = bytes([pay_load[i] ^ encoded[i] for i in range(260)])

        forged_crc = self.crc32(attack_msg)
        forged_payload = attack_msg + forged_crc
        forged_packet = iv + bytes([forged_payload[i] ^ key[i] for i in range(260)])

        return forged_packet

    def attack_two(self, ciphertext, attack_msg):
        # You may NOT use self.victim, since this is
        # a passive attack.

        ### Your cleverness here
        iv = ciphertext[:3]
        enc_plaintxt = ciphertext[3:-4]
        enc_plaintxt_crc = ciphertext[-4:]
        attack_msg_crc = self.crc32(attack_msg)
        zero_crc = self.crc32(bytes(len(attack_msg)))
        assert len(enc_plaintxt) == 256
        assert len(enc_plaintxt_crc) == 4
        assert len(attack_msg) == 256
        assert len(attack_msg_crc) == 4
        assert len(zero_crc) == 4
        forged_msg = bytes([enc_plaintxt[i] ^ attack_msg[i] for i in range(256)])
        forged_crc = bytes([enc_plaintxt_crc[i] ^ attack_msg_crc[i] ^ zero_crc[i] for i in range(4)])
        forged_packet = iv + forged_msg + forged_crc
        assert len(forged_packet) == 263

        return forged_packet

    def attack_three(self, target):
        # You may NOT call self.victim.send_packet() 
        # or self.victim.receive_packet() here.
        #
        # You may call self.victim.check_packet(),
        # defined in grader.py.
        
        ### Your cleverness here
        return guess_of_secret_msg
