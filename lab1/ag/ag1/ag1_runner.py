#!/usr/bin/env python3

import traceback
import random
from ag.ag1.ag1_storage import Lab1Storage
from ag.common.mock_http import link_client_server

from client import client
from server.reference_server import *
import common.types as types
import common.errors as errors
import common.codec as codec
import ag.common.util
from ag.common.testing import test_case

MAX_SCORE = 70

# tests from other files
from ag.ag1.fork_tests import test_single_photo_fork

### standard tests


@test_case(points=2)
def test_correct_behavior_1():
    """
    Tests that a client is able to put photos onto the server,
    and that they are listed properly by a second client.
    """
    pts = 2

    try:
        server = ReferenceServer()
        alice = client.Client("alice", server)
        link_client_server(alice, server)
        alice.register()
        user_secret = alice.user_secret
        alicebis = client.Client("alice", server, user_secret)
        link_client_server(alicebis, server)
        alicebis.login()
        alice.login()
        photo_blob1 = b"photo1"
        if alice.put_photo(photo_blob1) != 0:
            pts -= 1

        photo_blob2 = b"photo2"
        if alice.put_photo(photo_blob2) != 1:
            pts -= 1

        alicebis.login()
        photo_blob3 = b"photo3"
        if alicebis.put_photo(photo_blob3) != 2:
            pts -= 1

        photos = [photo_blob1, photo_blob2, photo_blob3]
        photo_list = alicebis.list_photos()
        alicebis_photos = []
        for pid in photo_list:
            alicebis_photos.append(alicebis.get_photo(pid))

        if photos != alicebis_photos:
            pts -= 1

        if pts < 0:
            pts = 0
        return pts
    except:
        traceback.print_exc()
        return 0


class ReplayLogEntryServer(ReferenceServer):
    """
    This server attempts to duplicate a photo by inserting
    the same log entry into the log twice for the photo with ID 1.
    """

    def put_photo_user(self, request):
        pass
        if not self._storage.check_token(request.username, request.token):
            return types.PutPhotoResponse(types.Errcode.INVALID_TOKEN, None)

        self._storage.store_photo(
            request.username, request.photo_id, request.photo_blob
        )
        self._storage.log_operation(request.username, request.encoded_log_entry)
        if request.photo_id == 1:
            # insert the same log entry a second time
            self._storage.log_operation(request.username, request.encoded_log_entry)

        return types.PutPhotoResponse(None)


@test_case(points=2)
def test_replay_attack_1():
    pts = 2

    try:
        server = ReplayLogEntryServer()
        alice_1 = client.Client("alice", server)
        link_client_server(alice_1, server)
        alice_1.register()
        user_secret = alice_1.user_secret
        alice_2 = client.Client("alice", server, user_secret)
        link_client_server(alice_2, server)
        alice_2.login()
        alice_1.login()
        photo_blob1 = b"photo1"
        if alice_1.put_photo(photo_blob1) != 0:
            pts -= 1

        alice_2.login()
        photo_blob2 = b"photo2"
        if alice_2.put_photo(photo_blob2) != 1:
            pts -= 1

        photo_blob3 = b"photo3"
        try:
            alice_2.put_photo(photo_blob3)
            pts -= 1
        except errors.SynchronizationError:  # TODO check the exact error
            pass

        if pts < 0:
            pts = 0
        return pts
    except:
        traceback.print_exc()
        return 0


class AllowDoubleRegisterServer(ReferenceServer):
    def register_user(self, request: types.RegisterRequest) -> types.RegisterResponse:
        if not self._storage.check_user_registered(request.username):
            token = secrets.token_hex(64)
            self._storage.add_new_user(request.username, request.auth_secret, token)
            self._storage.log_operation(request.username, request.encoded_log_entry)
            return types.RegisterResponse(None, token)
        else:
            # even if they already exist, register them again and return a new token
            token = secrets.token_hex(64)
            self._storage.log_operation(request.username, request.encoded_log_entry)
            return types.RegisterResponse(None, token)


@test_case(points=2)
def test_double_register_attack_2():
    pts = 2

    try:
        server = AllowDoubleRegisterServer()
        alice_1 = client.Client("alice", server)
        link_client_server(alice_1, server)
        alice_1.register()
        alice_1.login()

        photo_blob1 = b"photo1"
        if alice_1.put_photo(photo_blob1) != 0:
            pts -= 1

        user_secret = alice_1.user_secret
        alice_2 = client.Client("alice", server, user_secret)
        link_client_server(alice_2, server)
        alice_2.login()
        photo_blob2 = b"photo2"
        if alice_2.put_photo(photo_blob2) != 1:
            pts -= 1

        alice_1.register()

        alice_2.login()
        photo_blob3 = b"photo3"
        try:
            alice_2.put_photo(photo_blob3)
            pts = 0
        except errors.SynchronizationError:  # TODO make check more precise
            pass
        except:
            traceback.print_exc()
            pts = 0

        if pts < 0:
            pts = 0
        return pts

    except:
        traceback.print_exc()
        return 0


class ChangePhotoOrderServer(ReferenceServer):
    def __init__(self):
        self._storage = Lab1Storage()

    def put_photo_user(self, request: types.PutPhotoRequest) -> types.PutPhotoResponse:
        if not self._storage.check_token(request.username, request.token):
            return types.PutPhotoResponse(types.Errcode.INVALID_TOKEN, None)

        self._storage.store_photo(
            request.username, request.photo_id, request.photo_blob
        )

        if request.photo_id == 2:
            # switch the blobs for photo 2 and photo 1
            self._storage.swap_photo_blobs(request.username, 1, 2)

        self._storage.log_operation(request.username, request.encoded_log_entry)
        return types.PutPhotoResponse(None)


@test_case(points=2)
def test_change_photo_order_attack_1():
    """
    The server in this test switches the photo data for photo ID 1 and photo ID 2.
    The client should detect this and raise a SynchronizationError.
    """
    pts = 2

    try:
        server = ChangePhotoOrderServer()
        alice = client.Client("alice", server)
        link_client_server(alice, server)
        alice.register()
        alice.login()
        photo_blob1 = b"photo1"
        if alice.put_photo(photo_blob1) != 0:
            pts -= 1

        user_secret = alice.user_secret
        alice_2 = client.Client("alice", server, user_secret)
        link_client_server(alice_2, server)
        alice_2.login()

        photo_blob2 = b"photo2"
        if alice_2.put_photo(photo_blob2) != 1:
            pts -= 1

        alice.login()
        photo_blob3 = b"photo3"
        if alice.put_photo(photo_blob3) != 2:
            pts -= 1

        alice_2.login()
        photo_blob4 = b"photo4"
        try:
            alice_2.put_photo(photo_blob4)
            pts = 0
        except errors.SynchronizationError:  # TODO make check more exact
            pass
        except:
            traceback.print_exc()
            pts = 0

        if pts < 0:
            pts = 0
        return pts

    except:
        traceback.print_exc()
        return 0


class VersionNumberServer(ReferenceServer):
    def __init__(self):
        self._storage = Lab1Storage()

    def register_user(self, request: types.RegisterRequest) -> types.RegisterResponse:
        if not self._storage.check_user_registered(request.username):
            token = secrets.token_hex(64)
            self._storage.add_new_user(request.username, request.auth_secret, token)
            self._storage.log_operation(request.username, request.encoded_log_entry)
            return types.RegisterResponse(None, token)
        else:
            token = self._storage.get_user_token(request.username)
            return types.RegisterResponse(None, token)

    def synchronize(
        self, request: types.SynchronizeRequest
    ) -> types.SynchronizeResponse:
        if not self._storage.check_token(request.username, request.token):
            return types.SynchronizeResponse(types.Errcode.INVALID_TOKEN, None)

        # Check version compatibility
        server_version = self._storage.latest_user_version(request.username)

        if request.min_version_number > 0:
            return types.SynchronizeResponse(None, [])

        if request.min_version_number > server_version + 1:
            return types.SynchronizeResponse(types.Errcode.VERSION_TOO_HIGH, None)

        log = self._storage.user_history(request.username, request.min_version_number)
        return types.SynchronizeResponse(None, log)


@test_case(points=2)
def test_version_number_attack_1():
    """
    TODO: Figure out what this test actually does
    """
    pts = 2

    try:
        server = VersionNumberServer()
        alice = client.Client("alice", server)
        link_client_server(alice, server)
        alice.register()
        alice.login()

        user_secret = alice.user_secret
        alicecheck = client.Client("alice", server, user_secret)
        link_client_server(alicecheck, server)
        alicecheck.login()
        if alicecheck.list_photos() != []:
            pts -= 1

        alice.login()
        photo_blob1 = b"photo1"
        if alice.put_photo(photo_blob1) != 0:
            pts -= 1

        photo_blob2 = b"photo2"
        if alice.put_photo(photo_blob2) != 1:
            pts -= 1

        alice.register()

        photo_blob3 = b"photo3"
        if alice.put_photo(photo_blob3) != 2:
            pts -= 1

        alicebis = client.Client("alice", server, user_secret)
        link_client_server(alicebis, server)
        alicebis.login()
        photo_blob4 = b"photo4"
        try:
            alicebis.put_photo(photo_blob4)
            pts = 0
        except errors.SynchronizationError:  # TODO more precise check
            pass
        except:
            traceback.print_exc()
            pts = 0

        if pts < 0:
            pts = 0
        return pts

    except:
        traceback.print_exc()
        return 0


class ChangePhotoBlobServer(ReferenceServer):
    """
    This server changes the contents of a photo blob when it is retrieved.
    """

    def __init__(self):
        self._storage = Lab1Storage()

    def get_photo_user(self, request: types.GetPhotoRequest) -> types.GetPhotoResponse:
        if not self._storage.check_token(request.username, request.token):
            return types.GetPhotoResponse(types.Errcode.INVALID_TOKEN, None)

        photo = self._storage.load_photo(request.username, request.photo_id)

        if request.photo_id == 1:
            # replace photo 1's contents
            photo.photo_blob = b"photO2"

        if photo != None:
            return types.GetPhotoResponse(None, photo.photo_blob)
        else:
            return types.GetPhotoResponse(types.Errcode.PHOTO_DOES_NOT_EXIST, None)


@test_case(points=2)
def test_change_photo_blob_1():
    pts = 2

    try:
        server = ChangePhotoBlobServer()
        alice = client.Client("alice", server)
        link_client_server(alice, server)
        alice.register()
        alice.login()
        photo_blob1 = b"photo1"
        if alice.put_photo(photo_blob1) != 0:
            pts -= 1

        user_secret = alice.user_secret
        alicebis = client.Client("alice", server, user_secret)
        link_client_server(alicebis, server)
        alicebis.login()

        photo_blob2 = b"photo2"
        if alicebis.put_photo(photo_blob2) != 1:
            pts -= 1

        alice.login()
        photo_blob3 = b"photo3"
        try:
            alice.put_photo(photo_blob3)
            pts = 0
        except errors.SynchronizationError:  # TODO more precise check
            pass
        except:
            traceback.print_exc()
            pts = 0

        if pts < 0:
            pts = 0
        return pts

    except:
        traceback.print_exc()
        return 0


### trace tests


class StateTracer:
    def __init__(self, username, server):
        self.server = server
        self.write_client = client.Client(username, server)
        link_client_server(self.write_client, self.server)
        self.read_client = client.Client(
            username, server, self.write_client.user_secret
        )
        link_client_server(self.read_client, self.server)
        self.trace = []

    def register(self):
        self.write_client.register()
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
        self.trace.append(self._snapshot(self.write_client))

    def sanity_check(self):
        try:
            sanity_client = client.Client(
                self.write_client.username, self.server, self.write_client.user_secret
            )
            link_client_server(sanity_client, self.server)
            sanity_client.login()

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
    This is identical to the reference storage, but uses the testing version
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
        self._storage._map_log(request.username, request.photo_id, index)
        return types.PutPhotoResponse(None)


@test_case(points=2)
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


@test_case(points=2)
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


@test_case(points=2)
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


@test_case(points=2)
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


@test_case(points=2)
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


@test_case(points=2)
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
                types.OperationCode.PUT_PHOTO,
                types.OperationCode.REGISTER.value,
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
                attack.apply(server._storage)

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

