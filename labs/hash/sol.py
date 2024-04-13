from hashall import *
from hashbig import *
import os


# return password, where toy_hash(password) = e048903a3248
def problem_2a():
    for word in words:
        word = word.strip().lower()
        if toy_hash(word.encode('ascii')).hex() == 'e048903a3248':
            return word
    assert False, "not found"


# return password, where toy_hash(password) is in hashes.txt
def problem_2c():
    rainbow_table = set()
    with open("hashes.txt", "r") as f:
        for line in f:
            rainbow_table.add(line.strip())

    random_input = os.urandom(6)
    while True:
        hash = toy_hash(random_input).hex()
        if hash in rainbow_table:
            return random_input
        random_input = os.urandom(6)

# return probability of being in bin k
def problem_3a(B, N):
    return 1/N

# return probability of both balls being in bin k
def problem_3b(B,N):
    return 1/N**2

# return number of ball pairs
def problem_3c(B):
    return B*(B-1)/2

# return reasonable upper bound
def problem_3d(B,N):
    return B*(B-1)/2/N
    
# return reasonable upper bound
def problem_3e(L,N):
    return problem_3d(L, 2**N)

# return h1,h2 where H(h1) == H(h2)
def problem_4b():
    x0 = 'x0'.encode('ascii')  # Initial value
    
    tortoise = H(x0)
    hare = H(H(x0))
    
    # Phase 1: Detect Cycle
    while tortoise != hare:
        tortoise = H(tortoise)
        hare = H(H(hare))
    
    meet_point = tortoise
        
    # Phase 2: Find cycle length (lambda)
    cycle_len = 1
    x = H(meet_point)
    while x != meet_point:
        x = H(x)
        cycle_len += 1

    # Phase 3: Find Collision
    x, y = x0, x0
    for _ in range(cycle_len):
        y = H(y)
        
    pre_x, pre_y = x, y
    while x != y:
        pre_x = x
        pre_y = y
        x = H(x)
        y = H(y)

    return pre_x, pre_y