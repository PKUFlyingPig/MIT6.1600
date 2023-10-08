import base64
import binascii
import hmac
import paramiko
import threading

import constants

class Server(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()
        self.auth_type = None

    def check_auth_publickey(self, username_in, key_in):
        if username_in != constants.CLIENT_NAME:
            return paramiko.AUTH_FAILED

        with open(constants.CLIENT_PUB_KEY, "r") as f:
            parts = f.readline().split()
            (key_type, key_bytes) = parts[0:2]
            key = paramiko.PKey.from_type_string(key_type, base64.b64decode(key_bytes))

            if key_in == key:
                return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    # Allow public key authentication only
    def get_allowed_auths(self, username):
        return "publickey"

    ##
    # The code below allows clients to open interactive sessions
    # with the server.
    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

