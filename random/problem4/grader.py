import os
import traceback

from attacker import Attacker
from victim import Victim

def grade_one():
    v = Victim()
    plaintext = os.urandom(256)
    ciphertext = v.send_packet(plaintext)

    a = Attacker(None)
    packet = a.attack_one(plaintext, ciphertext)
    msg = v.receive_packet(packet)
    if msg is None:
        raise Exception("Victim rejected packet")
    if msg == plaintext:
        raise Exception("Forged message is not a new one")

def grade_two():
    v = Victim()
    plaintext = os.urandom(256)
    ciphertext = v.send_packet(secret_msg)

    a = Attacker(None)
    packet = a.attack_two(ciphertext)
    msg = v.receive_packet(packet)
    if msg is None:
        raise Exception("Victim rejected packet")
    if msg == plaintext:
        raise Exception("Forged message is not a new one")

def grade_three():
    v = Victim()

    plaintext = os.urandom(256)
    target_packet = v.send_packet(plaintext)

    a = Attacker(v)
    guess = a.attack_three(target_packet)

    if plaintext != guess:
        raise Exception("Incorrect guess")


checks = {
    "one": grade_one,
    "two": grade_two,
    "three": grade_three,
}

if __name__ == '__main__':
    for n, f in checks.items():
        try:
            f()
            print("%s: pass" % n)
        except:
            traceback.print_exc()
            print("%s: fail" % n)
