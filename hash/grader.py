from hashall import *
from hashbig import *
from sol import problem_2a, problem_2c, problem_4b, problem_3a, problem_3b, problem_3c, problem_3d, problem_3e

import traceback

def timeout(func, args=(), kwargs={}, timeout_duration=1, default=None):
    import signal
    class TimeoutError(Exception):
        pass

    def handler(signum, frame):
        raise TimeoutError()

    # set the timeout handler
    signal.signal(signal.SIGALRM, handler) 
    signal.alarm(timeout_duration)
    try:
        result = func(*args, **kwargs)
    finally:
        signal.alarm(0)

    return result

def test_2a():
    result = timeout(problem_2a,timeout_duration = 5*60)
    
    if(isinstance(result, str)):
        result = result.encode("ascii")

    target = "FIND ME ON GRADESCOPE"

    if toy_hash(result).hex() != target:
        raise Exception(f"toy_hash(password) outputs {toy_hash(result).hex()}, not {target}")


def test_2c():
    data_hash = set()

    with open("hashes.txt",'r') as data_file:
            for line in data_file:
                data_hash.add(line.strip())

    
    result = timeout(problem_2c,timeout_duration =10*60)


    if(isinstance(result, str)):
        result = result.encode("ascii")
  

    if toy_hash(result).hex() not in data_hash:
        raise Exception(f"toy_hash(password) = {toy_hash(result).hex()} is not found in the text file of hashes!")

def test_4b():
    a,b = timeout(problem_4b,timeout_duration =20*60)

    if H(a) !=  H(b):
        raise Exception(f"H({a}) = {H(a).hex()} != H({b}) = {H(b).hex()}")

def test_questions():
    file = open("questions.txt", "r")
    #read the content of file
    data = file.read()
    #get the length of the data
    number_of_characters = len(data)

    if(number_of_characters < 500):
        raise Exception("questions.txt not answered!")

checks = {
    "2a": test_2a,
    "2c": test_2c,
    "4b": test_4b,
    "questions": test_questions
}

if __name__ == '__main__':
    for n, f in checks.items():
        try:
            f()
            print("%s: pass" % n)
        except:
            traceback.print_exc()
            print("%s: fail" % n)