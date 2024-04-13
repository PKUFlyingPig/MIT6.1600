import os
import traceback

from attacker import Attacker
from victim import Victim

def grade_one():
    v = Victim()
    plaintext = os.urandom(256)
    ciphertext = v.send_packet(plaintext)
    attack_msg = os.urandom(256)

    a = Attacker(None)
    packet = a.attack_one(plaintext, ciphertext, attack_msg)
    msg = v.receive_packet(packet)
    if msg is None:
        raise Exception("Victim rejected packet")
    if msg != attack_msg:
        raise Exception("Forged message is incorrect")

def grade_two():
    v = Victim()
    plaintext = os.urandom(256)
    ciphertext = v.send_packet(plaintext)
    attack_xor = os.urandom(256)
    expected = bytes([plaintext[i] ^ attack_xor[i] for i in range(256)])

    a = Attacker(None)
    packet = a.attack_two(ciphertext, attack_xor)
    msg = v.receive_packet(packet)
    if msg is None:
        raise Exception("Victim rejected packet")
    if msg != expected:
        raise Exception("Forged message is incorrect")

def grade_three():
    v = Victim()

    plaintext = os.urandom(256)
    target_packet = v.send_packet(plaintext)
    f = v.receive_packet
    v.send_packet = None
    v.receive_packet = None

    # Returns the bit of whether victim accepted packet
    def check_packet(packet):
        return f(packet) != None
    v.check_packet = check_packet

    a = Attacker(v)
    guess = a.attack_three(target_packet)

    if plaintext != guess:
        raise Exception("Incorrect guess")

def test_questions():
    file = open("questions.txt", "r")
    #read the content of file
    data = file.read()
    #get the length of the data
    number_of_characters = len(data)

    if(number_of_characters < 500):
        raise Exception("questions.txt not answered!")

checks = {
    "one": grade_one,
    "two": grade_two,
    "three": grade_three,
    "questions": test_questions
}

if __name__ == '__main__':
    for n, f in checks.items():
        try:
            f()
            print("%s: pass" % n)
        except:
            traceback.print_exc()
            print("%s: fail" % n)
