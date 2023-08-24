import secrets
import api
from typing import Optional

class BadServer:
    def __init__(self, password: Optional[str] = None):
        if password is None:
            self._password = secrets.token_hex(256)
        else:
            self._password = password

    def send_money(self):
        # This is where the protected code would run.
        pass

    def verify_password(self, request: api.VerifyRequest) -> api.VerifyResponse:
        try:
            s = request.password
            for i in range(len(self._password)):
                if len(s) <= i:
                    return api.VerifyResponse(False)
                elif s[i] != self._password[i]:
                    return api.VerifyResponse(False)

            # At this point, the user is authenticated.
            self.send_money()

            return api.VerifyResponse(True)
        except:
            return api.VerifyResponse(False)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
