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

    if toy_hash(result).hex() != "a33a874eb313":
        raise Exception(f"toy_hash(password) outputs {toy_hash(result).hex()}, not a33a874eb313")


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

def test_3a():

    a_test = {
        (3,4): .25,
        (5,4): .25,
        (7,10): .1,
        (20,17): 0.05882352941
    }

    for in_test, answer in a_test.items():
        out = timeout(problem_3a ,args = in_test, timeout_duration = 2)
        if(abs(out-answer) > answer/100):
            raise Exception(f"3a({in_test}) = {out} which is incorrect.")

def test_3b():
    b_test = {
        (3,4): 0.0625,
        (5,4): 0.0625,
        (7,10): 0.01,
        (20,17): 0.00346020761
    }

    for in_test, answer in b_test.items():
        out = timeout(problem_3b ,args = in_test, timeout_duration = 2)
        if(abs(out-answer) > answer/100):
            raise Exception(f"3b({in_test}) = {out} which is incorrect.")

def test_3c():
    c_test = {
        3: 3,
        0: 0,
        5: 10,
        6: 15,
        204: 20706,
        312: 48516
    }

    for in_test, answer in c_test.items():
        out = timeout(problem_3c ,args = (in_test,), timeout_duration = 2)
        if(out != answer):
            raise Exception(f"3c({in_test}) = {out} which is incorrect.")

def test_3d(): 
    d_test = {
        (3,126): 0.023683547493071222,
        (5,98): 0.09844936538138971,
        (19,651): 0.2329451358309994,
        (20,781): 0.21755231339277203,
        (31, 1056): 0.35894664556915257,
        (347,798415): 0.07244074040833626
    }

    for in_test, answer in d_test.items():
        out = timeout(problem_3d ,args = in_test, timeout_duration = 2)
        if(out < answer or abs(out-answer)/answer > .25):
            raise Exception(f"3d({in_test}) = {out} which is incorrect.")

def test_3e():
     e_test = {
        (100,16): .0728,
        (500,32): 2.9045202102784273e-05,
        (255360000,64): 0.001765925,
        (85120000,64): 0.00019636,
    }

     for in_test, answer in e_test.items():
        out = timeout(problem_3e ,args = in_test, timeout_duration = 2)
        if(out < answer or abs(out-answer)/answer > .25):
            raise Exception(f"3e({in_test}) = {out} which is incorrect.")
    

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
    "3a": test_3a,
    "3b": test_3b,
    "3c": test_3c,
    "3d": test_3d,
    "3e": test_3e,
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