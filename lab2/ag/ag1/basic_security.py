import traceback
from ag.ag1.storage import Lab1Storage

from server.reference_server import *
import common.types as types
import common.errors as errors
from ag.common.testing import test_case
from ag.common.fixtures import new_authorized_device, new_client


@test_case(points=2, starter_points=2)
def test_correct_behavior_1():
    """
    Tests that a client is able to put photos onto the server,
    and that they are listed properly by a second client.
    """
    pts = 2

    try:
        server = ReferenceServer()
        alice = new_client(server, "alice")
        alice.register()
        alicebis = new_authorized_device(server, alice)
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


@test_case(points=2, starter_points=1)
def test_replay_attack_1():
    pts = 2

    try:
        server = ReplayLogEntryServer()
        alice_1 = new_client(server, "alice")
        alice_1.register()
        alice_2 = new_authorized_device(server, alice_1)

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
        alice_1 = new_client(server, "alice")
        alice_1.register()
        alice_1.login()

        photo_blob1 = b"photo1"
        if alice_1.put_photo(photo_blob1) != 0:
            pts -= 1

        alice_2 = new_authorized_device(server, alice_1)
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
        alice = new_client(server, "alice")
        alice.register()
        alice.login()
        photo_blob1 = b"photo1"
        if alice.put_photo(photo_blob1) != 0:
            pts -= 1

        alice_2 = new_authorized_device(server, alice)

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
        except errors.SynchronizationError:
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


class OmitSecondRegisterServer(ReferenceServer):
    """
    This server allows clients to double-register, but does not add the second
    registration request to the log.
    """

    def __init__(self):
        self._storage = Lab1Storage()
        self.double_registered_users: t.Set[str] = set()

    def register_user(self, request: types.RegisterRequest) -> types.RegisterResponse:
        if not self._storage.check_user_registered(request.username):
            token = secrets.token_hex(64)
            self._storage.add_new_user(request.username, request.auth_secret, token)
            self._storage.log_operation(request.username, request.encoded_log_entry)
            return types.RegisterResponse(None, token)
        else:
            self.double_registered_users.add(request.client_id)
            token = self._storage.get_user_token(request.username)
            return types.RegisterResponse(None, token)

    def synchronize(
        self, request: types.SynchronizeRequest
    ) -> types.SynchronizeResponse:
        if not self._storage.check_token(request.username, request.token):
            return types.SynchronizeResponse(types.Errcode.INVALID_TOKEN, None)

        # don't tell double registered clients about any new log entries after their first sync.
        # this is to avoid incompatible versioning when the client with an extra entry tries to sync
        if request.client_id in self.double_registered_users:
            return types.SynchronizeResponse(None, [])

        # on first sync, return the whole log
        log = self._storage.user_history(request.username, request.min_version_number)
        return types.SynchronizeResponse(None, log)


@test_case(points=2)
def test_missing_entry_1():
    """
    Here, alice tries to register twice but the server
    does not save the second register request. This means that
    alice's local log will differ from the log returned by the
    server: alice's local log will have a REGISTER entry that
    will not be delivered to a new device that tries to synchronize.
    This should be detected when the new device tries to synchronize.

    XXX: this test case tests behavior that is not defined by the spec
    (the spec talks only about photos)
    """
    pts = 2

    try:
        server = OmitSecondRegisterServer()
        alice = new_client(server, "alice")
        alice.register()
        alice.login()

        alicecheck = new_authorized_device(server, alice)
        alicebis = new_authorized_device(server, alicecheck)

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

        photo_blob4 = b"photo4"
        alicebis.login()
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
        alice = new_client(server, "alice")
        alice.register()
        alice.login()
        photo_blob1 = b"photo1"
        if alice.put_photo(photo_blob1) != 0:
            pts -= 1

        alicebis = new_authorized_device(server, alice)

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

