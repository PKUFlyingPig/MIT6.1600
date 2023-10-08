
def attack_decrypt(client_fn):
    # Your attack here.
    (bytes_out, bytes_in) = client_fn("prefix string")

    return "your guess of secret string"

class AttackTamper:
    def __init__(self):
        # Any state you need for the attack.
        pass

    def handle_data(self, data):
        # Your attack here.
        return data
