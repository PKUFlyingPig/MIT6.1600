import inspect
import os

def attack_one(guess):
    secret = guess.__closure__[0].cell_contents
    return secret

def attack_two():
    # Get the frame of the caller of the current function.
    caller_frame = inspect.currentframe().f_back
    # Access the local variables of the caller's frame.
    local_vars_in_caller = caller_frame.f_locals
    return local_vars_in_caller['secret']

def attack_three():
    def my_urandom(x):
        return b'no_random'
    os.urandom = my_urandom
    return b'no_random'

def attack_four():
    # Get hash value h
    caller_frame = inspect.currentframe().f_back
    h = caller_frame.f_locals['h']

    class my_sha256:
        def __init__(self, x) -> None:
            self.x = x
        
        def digest(self):
            return h
    import hashlib
    hashlib.sha256 = my_sha256

    return b''
