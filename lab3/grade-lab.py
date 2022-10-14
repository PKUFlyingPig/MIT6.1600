#!/usr/bin/env python3

import argparse
import importlib
import json
import ag.common.testing as testing


parser = argparse.ArgumentParser(description="Description of your program")
parser.add_argument(
    "-l", "--lab", help="The lab to grade (0, 1, 2, or 3)", required=True, type=int
)
parser.add_argument(
    "-j", "--json", help="Write JSON grade report to this file", required=False, type=str
)
parser.add_argument(
    "--staff", help="Expect full points", action="store_true"
)
parser.add_argument(
    "--starter", help="Expect zero points", action="store_true"
)
args = vars(parser.parse_args())

print("================================================================")
importlib.import_module('ag.ag{}.runner'.format(args["lab"]))
results = testing.run_tests()
print("================================================================")

json_out = args["json"]
if json_out is not None:
    with open(json_out, 'w') as f:
        f.write(json.dumps(results, indent=2))

if args["staff"]:
    if results["score"] != results["max_score"]:
        raise Exception("Staff solution did not get full points")

if args["starter"]:
    for t in results["tests"]:
        if t["score"] != t["starter_score"]:
            raise Exception("Starter solution got {} points for test case {}, expected {}".format(
                t["score"], t["name"], t["starter_score"]))
    if results["score"] != results["starter_score"]:
        raise Exception("Starter solution did not get the expected {} points".format(results["starter_score"]))

