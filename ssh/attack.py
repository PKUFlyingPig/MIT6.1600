
class AttackTamper:
    def __init__(self, compress):
        # compress is set for the last extra credit part
        self.compress = compress
        self.bytes = 0

    def handle_data(self, data):
        # Your attack here.
        return data

def attack_decrypt(client_fn):
    # Your attack here.
    (bytes_out, bytes_in) = client_fn("prefix string")

    return "your guess of secret string"

