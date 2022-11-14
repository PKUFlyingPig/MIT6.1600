import secure_server
import api
import secrets
from typing import Optional

class Client:
    def __init__(self, remote: secure_server.VerySecureServer):
        self._remote = remote

    def steal_secret_token(self, l: int) -> Optional[str]:
        secret_token = secrets.token_hex(l)
        req = api.VerifyTokenRequest(secret_token)
        if self._remote.verify_token(req).ret:
            return secret_token
        else:
            return None

if __name__ == "__main__":
    token = '37a4e5bf847630173da7e6d19991bb8d'
    nbytes = len(token) // 2
    server = secure_server.VerySecureServer(token)
    alice = Client(server)
    print(alice.steal_secret_token(nbytes))

