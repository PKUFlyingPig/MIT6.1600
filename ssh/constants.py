import os

THIS_DIR = os.path.dirname(__file__)

# Server's host key
SERVER_HOST_KEYFILE = os.path.join(THIS_DIR, "keys/server")

CLIENT_NAME = "alice"
CLIENT_PRIV_KEY = os.path.join(THIS_DIR, "keys/client")
CLIENT_PUB_KEY = os.path.join(THIS_DIR, "keys/client.pub")

PORT = 2200

BINGO = "Bingo!"
