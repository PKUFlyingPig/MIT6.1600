"""
A common API between the client and the server.
"""

class VerifyTokenRequest():
    def __init__(self, token: str):
        self.token = token

class VerifyTokenResponse():
    def __init__(self, ret: bool):
        self.ret = ret

