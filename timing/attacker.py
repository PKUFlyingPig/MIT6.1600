import bad_server
import api
import secrets
from typing import Optional

class Client:
    def __init__(self, remote: bad_server.BadServer):
        self._remote = remote

    def steal_password (self, l: int) -> Optional[str]:
        password = secrets.token_hex(l)
        req = api.VerifyRequest(password)
        if self._remote.verify_password(req).ret:
            return password
        else:
            return None

if __name__ == "__main__":
    passwd = '37a4e5bf847630173da7e6d19991bb8d'
    nbytes = len(passwd) // 2
    server = bad_server.BadServer(passwd)
    alice = Client(server)
    print(alice.steal_secret_token(nbytes))
