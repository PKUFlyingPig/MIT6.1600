
import paramiko
import socket
import traceback

import constants
import opts

# Accept all server keys -- bad idea in real client.
class AcceptPolicy(paramiko.client.MissingHostKeyPolicy):
    def missing_host_key(self, client, hostname, key):
        return

class SocketWrapper:
    def __init__(self, sock, handle_send):
        self.sock = sock
        self._closed = False
        self.bytes_out = 0
        self.bytes_in = 0
        self.handle_send = handle_send

    def close(self):
        self.sock.close()

    def recv(self, size):
        data = self.sock.recv(size)
        self.bytes_in += len(data)
        return data

    def send(self, b):
        self.bytes_out += len(b)
        try:
            b = self.handle_send(b)
        except:
            traceback.print_exc()
        return self.sock.send(b)

    def settimeout(self, t):
        return self.sock.settimeout(t)

def t_factory(sock, gss_kex, gss_deleg_creds, disabled_algorithms):
    t = paramiko.Transport(sock, gss_kex, gss_deleg_creds, disabled_algorithms)
    opts.disable_mac(t)

    return t

class Client:
    def __init__(self, handle_send = lambda x: x):
        self.handle_send = handle_send
        self.message_received = None

    # `run_client` takes as input a string `prefix`, opens an SSH
    # connection to the server, and sends the string `prefix+SECRET`
    # to the server. The function returns a tuple `(bytes_sent, bytes_received)`.
    def run_client(self, msg, compress):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("localhost", constants.PORT))
            b = SocketWrapper(s, self.handle_send)

            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(AcceptPolicy())
            client.connect(hostname = 'localhost',
                           port = constants.PORT,
                           username = constants.CLIENT_NAME,
                           key_filename = constants.CLIENT_PRIV_KEY,
                           compress = compress,
                           sock = b,
                           transport_factory = t_factory)

            chan = client.invoke_shell('')
            f = chan.makefile("Urw+")
            f.write(msg + "\n")
            self.message_received = f.readline().strip()
            client.close()

            return (b.bytes_out, b.bytes_in)

