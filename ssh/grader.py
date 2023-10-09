import attack
import client
import constants
import random

def get_countries():
    countries = []
    with open("capitals.txt", "r") as f:
        for line in f:
            countries.append(line.strip())
    return countries

def grade_decrypt():
    countries = get_countries()
    secret = "{\n"
    for i in range(3):
        secret += '"city%d": "%s",\n' % (i, random.choice(countries))
    secret += "}\n"

    c = client.Client()

    def run_client(prefix):
        return c.run_client(prefix + secret, compress=True)

    guess = attack.attack_decrypt(run_client)

    if secret != guess:
        raise ValueError("Bad guess")

def grade_tamper():
    a = attack.AttackTamper()
    c = client.Client(a.handle_data)
    c.run_client("ls ./files/*", compress=False)

    if c.message_received != constants.BINGO:
        raise ValueError("Not successful")


def main():
    parts = [
        ('a', grade_decrypt),
        ('b', grade_tamper),
    ]

    for p in parts:
        try:
            p[1]()
            print("Part (%s): Pass" % p[0])
        except ValueError:
            print("Part (%s): Fail" % p[0])


if __name__ == "__main__":
    main()
