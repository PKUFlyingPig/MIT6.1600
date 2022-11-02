import tempfile
import os
import os.path
import subprocess
import argparse
import json

parser = argparse.ArgumentParser(description="Grade lab 4")
parser.add_argument("-l", "--lab", help="The lab to grade (4)", type=int)
parser.add_argument("--json", help="Write JSON grade report to this file", type=str)
parser.add_argument("--staff", help="Expect full points", action="store_true")
parser.add_argument("--starter", help="Expect zero points", action="store_true")
args = vars(parser.parse_args())

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
            p = subprocess.run(["python", "shell.py", sh, sandbox], stdin=f, capture_output=True)
            print("  Secret found:", secret in p.stdout)
            if secret in p.stdout:
                return 1
            else:
                return 0

score_1 = grade_script('tinysh.wasm', 'solution-1.txt')
score_2 = grade_script('tinysh-noln.wasm', 'solution-2.txt')

results = {
    "max_score": 2,
    "score": score_1 + score_2,
    "starter_score": 0,
    "tests": [
        {
            "name": "solution-1.txt",
            "max_score": 1,
            "score": score_1,
            "starter_score": 0,
        },
        {
            "name": "solution-2.txt",
            "max_score": 1,
            "score": score_2,
            "starter_score": 0,
        },
    ],
}

json_out = args["json"]
if json_out is not None:
    with open(json_out, "w") as f:
        f.write(json.dumps(results, indent=2))

if args["staff"]:
    if results["score"] != results["max_score"]:
        raise Exception("Staff solution did not get full points")

if args["starter"]:
    if results["score"] != results["starter_score"]:
        raise Exception("Starter solution did not get the expected {} points".format(results["starter_score"]))

