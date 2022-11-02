import tempfile
import os
import subprocess

with tempfile.TemporaryDirectory() as d:
    secret = os.urandom(32).hex()
    with open(d + '/secret.txt', 'w') as f:
        f.write("The secret is %s\n" % secret)
    sandbox = d + '/sandbox'
    os.mkdir(sandbox)

    subprocess.run(["python", "shell.py", "tinysh.wasm", sandbox])

