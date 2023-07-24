import argparse
import binascii
import client
import common
import requests

class RemoteStore:
    def __init__(self, url):
        self._url = url.encode('utf-8')

    def proof(self, response):
        j = response.json()
        k = j.get('key')
        v = j.get('val')
        if k is not None: k = binascii.unhexlify(k)
        if v is not None: v = binascii.unhexlify(v)
        p = common.Proof(k, v, [binascii.unhexlify(s) for s in j['siblings']])
        return p

    def lookup(self, key):
        response = requests.get(b'%s/%s' % (self._url, binascii.hexlify(key)))
        return self.proof(response)

    def insert(self, key, val):
        response = requests.put(b'%s/%s' % (self._url, binascii.hexlify(key)), data=val)
        return self.proof(response)

    def reset(self):
        requests.post(b'%s/reset' % self._url, b'')

parser = argparse.ArgumentParser()
parser.add_argument("--server", default="http://localhost:5000", help="server URL")
parser.add_argument("--root-file", default="merkle.root", help="file containing merkle root")
parser.add_argument("cmd", help="get, put, or reset")
parser.add_argument("key", help="key to get or put", nargs="?")
parser.add_argument("value", help="value for put", nargs="?")
args = parser.parse_args()

s = RemoteStore(args.server)
try:
    with open(args.root_file, 'rb') as f:
        root_hash = binascii.unhexlify(f.readline().strip())
    client = client.Client(s, root_hash)
except FileNotFoundError:
    client = client.Client(s)

match args.cmd:
    case 'get':
        r = client.lookup(args.key.encode('utf-8'))
        if r is None:
            print(r)
        else:
            print(r.decode('utf-8'))
    case 'put':
        client.insert(args.key.encode('utf-8'), args.value.encode('utf-8'))
    case 'reset':
        client.reset()
    case _:
        parser.print_help()

with open(args.root_file, 'wb') as f:
    f.write(b'%s\n' % binascii.hexlify(client._root_hash))
