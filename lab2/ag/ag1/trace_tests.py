import traceback
import random
from ag.ag1.storage import Lab1Storage

from server.reference_server import *
import common.types as types
import common.errors as errors
import common.codec as codec
import ag.common.util
from ag.common.testing import test_case
from ag.common.fixtures import new_authorized_device, new_client, new_device

from client import client

### trace tests


class StateTracer:
    def __init__(self, username, server):
        self.server = server
        self.write_client = new_client(server, username)
        self.read_client = new_device(server, self.write_client)
        self.trace = []

    def register(self):
        self.write_client.register()
        self.write_client.login()
        self.write_client.invite_device(self.read_client.public_key)
        self.read_client.login()
        self.read_client.accept_invite(self.write_client.public_key)
        self._save_snapshot()

    def put_photo(self, blob):
        self.write_client.put_photo(blob)
        self._save_snapshot()

    def _snapshot(self, client):
        snapshot = []
        id_list = client.list_photos()
        for photo_id in id_list:
            snapshot.append(client.get_photo(photo_id))
        return snapshot

    def _save_snapshot(self):
        self.write_client.login()
        self.trace.append(self._snapshot(self.write_client))

    def sanity_check(self):
        try:
            sanity_client = new_authorized_device(self.server, self.write_client)

            snapshot = self._snapshot(sanity_client)
            return snapshot == self.trace[-1]
        except Exception:
            traceback.print_exc()
            return False

    def test_sync(self):
        self.read_client.login()
        try:
            snapshot = self._snapshot(self.read_client)
        except errors.SynchronizationError:
            self.server.synchronize = lambda request: types.SynchronizeResponse(
                None, []
            )
            try:
                snapshot = self._snapshot(self.read_client)
            except errors.SynchronizationError:
                # occurs when registration was tampered with
                return True
            pass

        for t_snapshot in self.trace:
            if t_snapshot == snapshot:
                return True

        # print('snapshot prefix invalid: {} does not precede {}'.format(snapshot, self.trace[-1]))
        return False


from enum import IntEnum, auto, unique


@unique
class TamperOp(IntEnum):
    REPLAY_LOG = auto()
    DELETE_LOG = auto()
    OVERWRITE_LOG = auto()
    SWAP_LOGS = auto()

    TAMPER_BLOB = auto()
    ZERO_BLOB = auto()

    SWAP_BLOBS = auto()
    SWAP_IDS = auto()

    INCR_INT = auto()
    DECR_INT = auto()
    TAMPER_INT = auto()
    ZERO_INT = auto()
    SWAP_INTS_0 = auto()


class StorageMod:
    def __init__(self, op, log_index, log_index2, int_offset, int_offset2):
        self.op = op
        self.log_index = log_index
        self.log_index2 = log_index2
        self.int_offset = int_offset
        self.int_offset2 = int_offset2

    def __str__(self):
        return f"StorageMod(op={self.op}, log_index={self.log_index}, log_index2={self.log_index2}, int_offset={self.int_offset}, int_offset={self.int_offset2})"

    def apply(self, storage):
        pid = self.log_index
        if pid == 0:
            pid = 1
        pid2 = self.log_index2
        if pid2 == 0:
            pid2 = 1

        if self.op == TamperOp.REPLAY_LOG:
            for username in storage.userbase:
                udata = storage.userbase[username]
                storage.userbase[username] = replay_log(udata, self.log_index)
        elif self.op == TamperOp.DELETE_LOG:
            for username in storage.userbase:
                udata = storage.userbase[username]
                storage.userbase[username] = delete_log(udata, self.log_index)
        elif self.op == TamperOp.OVERWRITE_LOG:
            for username in storage.userbase:
                udata = storage.userbase[username]
                storage.userbase[username] = overwrite_log(
                    udata, self.log_index, self.log_index2
                )
        elif self.op == TamperOp.SWAP_LOGS:
            for username in storage.userbase:
                udata = storage.userbase[username]
                storage.userbase[username] = swap_logs(
                    udata, self.log_index, self.log_index2
                )
        elif self.op == TamperOp.TAMPER_BLOB:
            for username in storage.userbase:
                blob_tamper(storage, username, pid)
        elif self.op == TamperOp.ZERO_BLOB:
            for username in storage.userbase:
                blob_zero(storage, username, pid)

        elif self.op == TamperOp.SWAP_BLOBS:
            for username in storage.userbase:
                swap_blobs(storage, username, pid, pid2)
        elif self.op == TamperOp.SWAP_IDS:
            for username in storage.userbase:
                swap_ids(storage, username, pid, pid2)

        elif self.op == TamperOp.INCR_INT:
            for username in storage.userbase:
                udata = storage.userbase[username]
                xs = find_ints(udata.history[self.log_index])
                if len(xs) == 0:
                    return
                off = self.int_offset % len(xs)
                storage.userbase[username] = replace_int(
                    udata, self.log_index, xs[off], xs[off] + 1
                )
        elif self.op == TamperOp.DECR_INT:
            for username in storage.userbase:
                udata = storage.userbase[username]
                xs = find_ints(udata.history[self.log_index])
                if len(xs) == 0:
                    return
                off = self.int_offset % len(xs)

                # TODO should we sanitize this?
                result = xs[off] - 1
                if result < 0:
                    result = 0

                storage.userbase[username] = replace_int(
                    udata, self.log_index, xs[off], result
                )
        elif self.op == TamperOp.TAMPER_INT:
            for username in storage.userbase:
                udata = storage.userbase[username]
                xs = find_ints(udata.history[self.log_index])
                if len(xs) == 0:
                    return
                off = self.int_offset % len(xs)
                storage.userbase[username] = replace_int(
                    udata, self.log_index, xs[off], self.int_offset2
                )
        elif self.op == TamperOp.ZERO_INT:
            for username in storage.userbase:
                udata = storage.userbase[username]
                xs = find_ints(udata.history[self.log_index])
                if len(xs) == 0:
                    return
                off = self.int_offset % len(xs)
                storage.userbase[username] = replace_int(
                    udata, self.log_index, xs[off], 0
                )
        elif self.op == TamperOp.SWAP_INTS_0:
            for username in storage.userbase:
                udata = storage.userbase[username]
                xs = find_ints(udata.history[self.log_index])
                if len(xs) == 0:
                    return
                off = self.int_offset % len(xs)
                off2 = self.int_offset2 % len(xs)
                storage.userbase[username] = replace_int(
                    udata, self.log_index, xs[off], xs[off2]
                )


def gen_index(gen_int, log_size):
    if gen_int(4) == 0:
        return 0
    else:
        return gen_int(log_size)


def gen_storage_mod(gen_int, log_size):
    op = TamperOp(1 + gen_int(len(TamperOp.__members__) - 1))
    log_index = gen_index(gen_int, log_size)
    log_index2 = gen_index(gen_int, log_size)
    int_offset = gen_int(50)
    int_offset2 = gen_int(50)
    return StorageMod(op, log_index, log_index2, int_offset, int_offset2)


def find_ints(log_entry):
    o = codec.decode(log_entry)
    return [x for x in ag.common.util.flatten(o) if type(x) == int]


def blob_zero(storage, username, id1):
    blob1 = storage.userbase[username].photobase[id1].photo_blob
    blob_tamper = b""

    storage.userbase[username].photobase[id1] = PhotoData(username, id1, blob_tamper)

    index1 = storage.photo_id_to_log_index[(username, id1)]

    udata = storage.userbase[username]
    udata = replace_bytes(udata, index1, blob1, blob_tamper)
    storage.userbase[username] = udata


def blob_tamper(storage, username, id1):
    blob1 = storage.userbase[username].photobase[id1].photo_blob
    blob_tamper = b"TAMPER" + blob1 + b"TAMPER"

    storage.userbase[username].photobase[id1] = PhotoData(username, id1, blob_tamper)

    index1 = storage.photo_id_to_log_index[(username, id1)]

    udata = storage.userbase[username]
    udata = replace_bytes(udata, index1, blob1, blob_tamper)
    storage.userbase[username] = udata


def replace_int(userdata, index, a, b):
    history = userdata.history
    log_entry = history[index]

    o = codec.decode(log_entry)
    o = ag.common.util.replace_val(o, a, b)
    log_entry = codec.encode(o)

    history = history[:index] + [log_entry] + history[index + 1 :]
    userdata.history = history
    return userdata


def replace_bytes(userdata, index, a, b):
    history = userdata.history
    log_entry = history[index]

    o = codec.decode(log_entry)
    o = ag.common.util.replace_val(o, a, b)
    log_entry = codec.encode(o)

    history = history[:index] + [log_entry] + history[index + 1 :]
    userdata.history = history
    return userdata


def swap_blobs(storage, username, id1, id2):
    blob1 = storage.userbase[username].photobase[id1].photo_blob
    blob2 = storage.userbase[username].photobase[id2].photo_blob

    storage.userbase[username].photobase[id1] = PhotoData(username, id1, blob2)
    storage.userbase[username].photobase[id2] = PhotoData(username, id2, blob1)

    index1 = storage.photo_id_to_log_index[(username, id1)]
    index2 = storage.photo_id_to_log_index[(username, id2)]

    udata = storage.userbase[username]
    udata = replace_bytes(udata, index1, blob1, blob2)
    udata = replace_bytes(udata, index2, blob2, blob1)
    storage.userbase[username] = udata


def swap_ids(storage, username, id1, id2):
    blob1 = storage.userbase[username].photobase[id1].photo_blob
    blob2 = storage.userbase[username].photobase[id2].photo_blob

    storage.userbase[username].photobase[id1] = PhotoData(username, id2, blob1)
    storage.userbase[username].photobase[id2] = PhotoData(username, id1, blob2)

    index1 = storage.photo_id_to_log_index[(username, id1)]
    index2 = storage.photo_id_to_log_index[(username, id2)]

    udata = storage.userbase[username]
    udata = replace_int(udata, index1, id1, id2)
    udata = replace_int(udata, index2, id2, id1)
    storage.userbase[username] = udata


def replay_log(userdata, index):
    history = userdata.history
    history = history[:index] + [history[index]] + history[index:]
    userdata.history = history
    return userdata


def delete_log(userdata, index):
    history = userdata.history
    history = history[:index] + history[index + 1 :]
    userdata.history = history
    return userdata


def overwrite_log(userdata, index_remove, index_replace):
    history = userdata.history
    history = (
        history[:index_remove] + [history[index_replace]] + history[index_remove + 1 :]
    )
    userdata.history = history
    return userdata


def swap_logs(userdata, index1, index2):
    history = userdata.history
    log1 = history[index1]
    log2 = history[index2]
    history = history[:index1] + [log1] + history[index1 + 1 :]
    history = history[:index2] + [log2] + history[index2 + 1 :]
    userdata.history = history
    return userdata


class TestServer(ReferenceServer):
    """
    This is identical to the reference server, but uses the testing version
    of the in-memory storage in order to run the test cases.
    """

    def __init__(self):
        self._storage = Lab1Storage()

    def put_photo_user(self, request: types.PutPhotoRequest) -> types.PutPhotoResponse:
        if not self._storage.check_token(request.username, request.token):
            return types.PutPhotoResponse(types.Errcode.INVALID_TOKEN, None)

        self._storage.store_photo(
            request.username, request.photo_id, request.photo_blob
        )
        index = self._storage.log_operation(request.username, request.encoded_log_entry)
        self._storage._map_log(request.username, index, request.photo_id)
        return types.PutPhotoResponse(None)


@test_case(points=2, starter_points=2)
def test_correct_behavior_1t():
    pts = 2

    try:
        server = TestServer()

        tracer = StateTracer("alice", server)
        tracer.register()

        for i in range(10):
            photo_blob = b"photo" + bytes(str(i), "utf-8")
            tracer.put_photo(photo_blob)
        if not tracer.sanity_check():
            return 0

        res = tracer.test_sync()
        if res:
            try:
                snap = tracer._snapshot(tracer.read_client)
                if snap != tracer.trace[-1]:
                    return 0
            except:
                traceback.print_exc()
                return 0
            return 2
        else:
            return 0
    except:
        traceback.print_exc()
        return 0


@test_case(points=2)
def test_replay_attack_1t():
    pts = 2

    try:
        server = TestServer()

        tracer = StateTracer("alice", server)
        tracer.register()

        for i in range(10):
            photo_blob = b"photo" + bytes(str(i), "utf-8")
            tracer.put_photo(photo_blob)
        if not tracer.sanity_check():
            return 0

        for username in server._storage.userbase:
            udata = server._storage.userbase[username]
            server._storage.userbase[username] = replay_log(udata, 5)

        res = tracer.test_sync()
        if res:
            return 2
        else:
            return 0
    except:
        traceback.print_exc()
        return 0


@test_case(points=2, starter_points=2)
def test_double_register_attack_2t():
    pts = 2

    try:
        server = TestServer()

        tracer = StateTracer("alice", server)
        tracer.register()

        for i in range(10):
            photo_blob = b"photo" + bytes(str(i), "utf-8")
            tracer.put_photo(photo_blob)
        if not tracer.sanity_check():
            return 0

        for username in server._storage.userbase:
            udata = server._storage.userbase[username]
            server._storage.userbase[username] = replay_log(udata, 0)

        res = tracer.test_sync()
        if res:
            return 2
        else:
            return 0
    except:
        traceback.print_exc()
        return 0


@test_case(points=2, starter_points=2)
def test_change_photo_id_attack_1t():
    pts = 2

    try:
        server = TestServer()

        tracer = StateTracer("alice", server)
        tracer.register()

        for i in range(10):
            photo_blob = b"photo" + bytes(str(i), "utf-8")
            tracer.put_photo(photo_blob)
        if not tracer.sanity_check():
            return 0

        for username in server._storage.userbase:
            udata = server._storage.userbase[username]
            server._storage.userbase[username] = replace_int(udata, 4, 3, 2)

        res = tracer.test_sync()
        if res:
            return 2
        else:
            return 0
    except:
        traceback.print_exc()
        return 0


@test_case(points=2, starter_points=2)
def test_change_photo_id_attack_2t():
    pts = 2

    try:
        server = TestServer()

        tracer = StateTracer("alice", server)
        tracer.register()

        for i in range(10):
            photo_blob = b"photo" + bytes(str(i), "utf-8")
            tracer.put_photo(photo_blob)
        if not tracer.sanity_check():
            return 0

        for username in server._storage.userbase:
            udata = server._storage.userbase[username]
            server._storage.userbase[username] = replace_int(udata, 4, 3, 300)

        res = tracer.test_sync()
        if res:
            return 2
        else:
            return 0
    except:
        traceback.print_exc()
        return 0


@test_case(points=2)
def test_change_photo_order_attack_1t():
    pts = 2

    try:
        server = TestServer()

        tracer = StateTracer("alice", server)
        tracer.register()

        for i in range(10):
            photo_blob = b"photo" + bytes(str(i), "utf-8")
            tracer.put_photo(photo_blob)
        if not tracer.sanity_check():
            return 0

        for username in server._storage.userbase:
            swap_blobs(server._storage, username, 4, 5)

        res = tracer.test_sync()
        if res:
            return 2
        else:
            return 0
    except:
        traceback.print_exc()
        return 0


@test_case(points=2)
def test_delete_log_1t():
    pts = 2

    try:
        server = TestServer()

        tracer = StateTracer("alice", server)
        tracer.register()

        for i in range(10):
            photo_blob = b"photo" + bytes(str(i), "utf-8")
            tracer.put_photo(photo_blob)
        if not tracer.sanity_check():
            return 0

        for username in server._storage.userbase:
            udata = server._storage.userbase[username]
            server._storage.userbase[username] = delete_log(udata, 5)

        res = tracer.test_sync()
        if res:
            return 2
        else:
            return 0
    except:
        traceback.print_exc()
        return 0


@test_case(points=2, starter_points=2)
def test_version_number_attack_2t_1():
    pts = 2

    try:
        server = TestServer()

        tracer = StateTracer("alice", server)
        tracer.register()

        for i in range(10):
            photo_blob = b"photo" + bytes(str(i), "utf-8")
            tracer.put_photo(photo_blob)
        if not tracer.sanity_check():
            return 0

        for username in server._storage.userbase:
            udata = server._storage.userbase[username]
            server._storage.userbase[username] = replace_int(udata, 4, 4, 2)

        res = tracer.test_sync()
        if res:
            return 2
        else:
            return 0
    except:
        traceback.print_exc()
        return 0


@test_case(points=2, starter_points=2)
def test_version_number_attack_2t_2():
    pts = 2

    try:
        server = TestServer()

        tracer = StateTracer("alice", server)
        tracer.register()

        for i in range(10):
            photo_blob = b"photo" + bytes(str(i), "utf-8")
            tracer.put_photo(photo_blob)
        if not tracer.sanity_check():
            return 0

        for username in server._storage.userbase:
            udata = server._storage.userbase[username]
            server._storage.userbase[username] = replace_int(udata, 4, 4, 200)

        res = tracer.test_sync()
        if res:
            return 2
        else:
            return 0
    except:
        traceback.print_exc()
        return 0


@test_case(points=2)
def test_change_photo_blob_1t():
    pts = 2

    try:
        server = TestServer()

        tracer = StateTracer("alice", server)
        tracer.register()

        for i in range(10):
            photo_blob = b"photo" + bytes(str(i), "utf-8")
            tracer.put_photo(photo_blob)
        if not tracer.sanity_check():
            return 0

        for username in server._storage.userbase:
            blob_tamper(server._storage, username, 1)

        res = tracer.test_sync()
        if res:
            return 2
        else:
            return 0
    except:
        traceback.print_exc()
        return 0


@test_case(points=2)
def test_censor_photo_1t():
    pts = 2

    try:
        server = TestServer()

        tracer = StateTracer("alice", server)
        tracer.register()

        for i in range(10):
            photo_blob = b"photo" + bytes(str(i), "utf-8")
            tracer.put_photo(photo_blob)
        if not tracer.sanity_check():
            return 0

        for username in server._storage.userbase:
            udata = server._storage.userbase[username]
            server._storage.userbase[username] = replace_int(
                udata,
                5,
                client.OperationCode.PUT_PHOTO,
                client.OperationCode.REGISTER.value,
            )

        # for username in server._storage.userbase:
        #     udata = server._storage.userbase[username]
        #     server._storage.userbase[username] = overwrite_log(udata, 5, 0)

        res = tracer.test_sync()
        if res:
            return 2
        else:
            return 0
    except:
        traceback.print_exc()
        return 0


@test_case(points=10)
def test_search_for_attacks_1t():
    pts = 10
    wrong = search_for_attacks(pts=pts, seed=65060, iters=50, logsize=5, muts=1)
    if wrong > pts:
        return 0
    else:
        return pts - wrong


@test_case(points=10)
def test_search_for_attacks_2t():
    pts = 10
    wrong = search_for_attacks(pts=pts, seed=65060, iters=50, logsize=5, muts=2)
    if wrong > pts:
        return 0
    else:
        return pts - wrong


@test_case(points=10)
def test_search_for_attacks_3t():
    pts = 10
    wrong = search_for_attacks(pts=pts, seed=65060, iters=50, logsize=10, muts=5)
    if wrong > pts:
        return 0
    else:
        return pts - wrong


def search_for_attacks(pts, seed, iters, logsize, muts):
    rng = random.Random(seed)

    def rng_int(b):
        return rng.randrange(0, b)

    correct = 0
    for i in range(iters):
        try:
            server = TestServer()

            tracer = StateTracer("alice", server)
            tracer.register()

            for j in range(logsize):
                photo_blob = b"photo" + bytes(str(j), "utf-8")
                tracer.put_photo(photo_blob)
            if not tracer.sanity_check():
                print("failed correct trace (length {})".format(logsize))
                if i - correct >= pts:
                    break
                continue

            attacks = []
            for j in range(muts):
                attacks.append(gen_storage_mod(rng_int, logsize))

            for attack in attacks:
                try:
                    attack.apply(server._storage)
                except:
                    print("ERROR: Error in test case. This will not affect your score, but please notify staff with the following:")
                    traceback.print_exc()

            try:
                res = tracer.test_sync()
            except:
                traceback.print_exc()
                res = False
            if res:
                correct += 1
            else:
                print(
                    "attack trace\n" + "\n".join("  " + str(smod) for smod in attacks)
                )

            if i - correct >= pts:
                break

        except:
            traceback.print_exc()
            pass

    # return pts * (float(correct) / iters)
    return iters - correct


# TODO multiuser attack?

