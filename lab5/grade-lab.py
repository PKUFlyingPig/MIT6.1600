import secure_server
import attacker
import secrets
import argparse
import json

parser = argparse.ArgumentParser(description="Grade lab 5")
parser.add_argument("-l", "--lab", help="The lab to grade (5)", type=int)
parser.add_argument("--json", help="Write JSON grade report to this file", type=str)
parser.add_argument("--staff", help="Expect full points", action="store_true")
parser.add_argument("--starter", help="Expect zero points", action="store_true")
args = vars(parser.parse_args())

def extract_bytes(n_bytes):
    secret = secrets.token_hex(n_bytes)
    server = secure_server.VerySecureServer(secret)
    attack = attacker.Client(server)
    res = attack.steal_secret_token(n_bytes)
    return res == secret

tests = [
    (50, 8),
    (25, 16),
    (15, 32),
    (10, 64),
]

test_results = []

for (pts, nbytes) in tests:
    print("Testing extract_bytes(%d) for %d points.." % (nbytes, pts))
    ok = extract_bytes(nbytes)
    print("Result:", ok)
    score = 0
    if ok:
        score = pts
    res = {
        "name": "extract_bytes(%d)" % nbytes,
        "max_score": pts,
        "score": score,
        "starter_score": 0,
    }
    test_results.append(res)

results = {
    "max_score": sum([r["max_score"] for r in test_results]),
    "score": sum([r["score"] for r in test_results]),
    "starter_score": sum([r["starter_score"] for r in test_results]),
    "tests": test_results,
}

print("%d / %d points" % (results["score"], results["max_score"]))

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

