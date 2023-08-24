"""
A common API between the client and the server.
"""

class VerifyRequest():
    def __init__(self, password: str):
        self.password = password

class VerifyResponse():
    def __init__(self, ret: bool):
        self.ret = ret
