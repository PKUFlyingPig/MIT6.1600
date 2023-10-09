
class NoneHash():
    def __init__(self):
        self.digest_size = 20
        self.block_size = 64

    def update(self, data):
        pass

    def digest(self):
        return b'\x00' * 20

    def copy(self):
        return NoneHash()

def disable_mac(t):
    t.use_compression(True)
    t._preferred_macs = ("none",)
    t._mac_info["none"] = {"class": NoneHash, "size": 20}
    return t

