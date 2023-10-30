import tempfile
import os
import os.path
import subprocess
import traceback
import sys
import hashlib

def grade_script(sh, script_fn):
    print("Checking", script_fn, "using", sh)
    if not os.path.exists(script_fn):
        print("  File does not exist:", script_fn)
        return 0

    with tempfile.TemporaryDirectory() as d:
        secret = os.urandom(32).hex().encode('utf-8')
        with open(d + '/secret.txt', 'wb') as f:
            f.write(b"The secret is %s\n" % secret)
        sandbox = d + '/sandbox'
        os.mkdir(sandbox)

        with open(script_fn, 'rb') as f:
            p = subprocess.run([sys.executable, "shell.py", sh, sandbox], stdin=f, capture_output=True)
            print("  Secret found:", secret in p.stdout)
            if secret not in p.stdout:
                raise Exception("secret not printed")

def escape_one():
    grade_script('tinysh.wasm', 'solution-1.txt')

def escape_two():
    grade_script('tinysh-noln.wasm', 'solution-2.txt')

def check_sandbox():
    r = os.urandom(1024)

    import sandbox
    h0 = sandbox.sha256(r)
    h1 = hashlib.sha256(r).digest()

    if type(h0) != type(h1) or h0 != h1:
        raise Exception("did not return correct hash")

checks = {
    "escape-1": escape_one,
    "escape-2": escape_two,
    "sandbox": check_sandbox,
}

if __name__ == '__main__':
    for n, f in checks.items():
        try:
            f()
            print("%s: pass" % n)
        except:
            traceback.print_exc()
            print("%s: fail" % n)
