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

    def local_verify_password(self, request: api.VerifyRequest) -> api.VerifyResponse:
        fake_password = '37a4e5bf847630173da7e6d19991bb8d'
        try:
            s = request.password
            for i in range(len(fake_password)):
                if len(s) <= i:
                    # print(f"{i}: {s[i]}")
                    return api.VerifyResponse(False)
                elif s[i] != fake_password[i]:
                    # print(f"{i}: {s[i]}")
                    return api.VerifyResponse(False)
                # print(f"{i}: {s[i]}")
            return api.VerifyResponse(True)
        except Exception as e:
            print(e)
            return api.VerifyResponse(False)

    def measure_time(self, password: str, outer_iters = 5, inner_iters=5000, is_last_char=False) -> float:
        if is_last_char:
            req = api.VerifyRequest(password)
        else:
            req = api.VerifyRequest(password+"xx")
            
        times = []
        # warmup
        for _ in range(10):
            self._remote.verify_password(req)
            # self.local_verify_password(req)
        for _ in range(outer_iters):
            start_time = time.time()
            for _ in range(inner_iters):
                self._remote.verify_password(req)
            # self.local_verify_password(req)
            end_time = time.time()
            times.append(end_time - start_time)
        times.sort()
        median = times[outer_iters//2]
        return median

    def get_next_char(self, loc: int, l: int, cur_password: str) -> str:
        hex_chars = "0123456789abcdef"
        measured_times = dict.fromkeys(hex_chars, 0)

        is_last_char = (loc==2*l-1)
        outer_iters = 5
        if loc <= 16:
            inner_iters = 10000
        elif loc <= 32:
            inner_iters = 20000
        else:
            inner_iters = 40000
        
        winner_counts = dict.fromkeys(hex_chars, 0)
        for _ in range(20):
            for ch in hex_chars:
                cur_time = self.measure_time(cur_password, outer_iters=outer_iters, inner_iters=inner_iters, is_last_char=is_last_char)
                test_password = cur_password + ch
                test_time = self.measure_time(test_password, outer_iters=outer_iters, inner_iters=inner_iters, is_last_char=is_last_char)
                t = test_time - cur_time
                measured_times[ch] = t
            
            next_char = max(measured_times, key=measured_times.get)
            winner_counts[next_char] += 0.5
            sorted_items = sorted(measured_times.items(), key=lambda x: x[1], reverse=True)
            conf = sorted_items[0][1] / sorted_items[1][1]
            if conf >= 3 and conf <= 8 and max(winner_counts, key=winner_counts.get) == next_char and not is_last_char:
                winner_counts[next_char] += 100
                break

        # winner = max(winner_counts, key=winner_counts.get)
        winner = next_char
        return winner, measured_times, sorted_items

    def steal_password(self, l: int) -> str:
        passwd = 'f65bdbeea82bf1ec25d90f984861281d'
        stolen_password = ''
        for i in range(l * 2):  # Two hex chars for each byte
            next_char, measured_times, candidates = self.get_next_char(i, l, stolen_password)
            stolen_password += next_char
            print(f"true {i}: {passwd[i]}, measured: {measured_times[passwd[i]]}")
            print(f"candi 0: {candidates[0][0]}, measured: {measured_times[candidates[0][0]]}, conf: {measured_times[candidates[0][0]] / measured_times[candidates[1][0]]}")
            print(f"candi 1: {candidates[1][0]}, measured: {measured_times[candidates[1][0]]}, conf: {measured_times[candidates[1][0]] / measured_times[candidates[2][0]]}")
            print(f"candi 2: {candidates[2][0]}, measured: {measured_times[candidates[2][0]]}, conf: {measured_times[candidates[2][0]] / measured_times[candidates[3][0]]}")
            print()

        return stolen_password

if __name__ == "__main__":
    passwd = 'f65bdbeea82bf1ec25d90f984861281d'
    nbytes = len(passwd) // 2
    server = bad_server.BadServer(passwd)
    alice = Client(server)
    stole = alice.steal_password(nbytes)
    print("passwd: ", passwd)
    print("stolen: ", stole)
