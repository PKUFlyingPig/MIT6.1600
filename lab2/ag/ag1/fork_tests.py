import traceback
import typing as t
from ag.common.fixtures import new_authorized_device, new_client

from server.reference_server import InMemoryStorage, ReferenceServer
from server.types import PhotoData
import common.types as types
import common.errors as errors
from ag.common.testing import test_case
from ag.common.mock_http import link_client_server

from client import client


class ForkServer(ReferenceServer):
    """
    This server allows each client to upload a different
    version of photo ID 1, but then provides only the first client's
    version of photo 2 to both clients.
    """

    def __init__(self) -> None:
        super().__init__()
        self.alternate_log_entries: t.Dict[
            str, t.Tuple[bytes, PhotoData]
        ] = {}  # stores alternate photo ID 1 (log entry, photo) for each client id

    def put_photo_user(self, request: types.PutPhotoRequest) -> types.PutPhotoResponse:
        if not self._storage.check_token(request.username, request.token):
            return types.PutPhotoResponse(types.Errcode.INVALID_TOKEN, None)

        if request.photo_id == 1:
            self.alternate_log_entries[request.client_id] = (
                request.encoded_log_entry,
                PhotoData(request.username, request.photo_id, request.photo_blob),
            )
            if len(self.alternate_log_entries) > 1:
                # if we already have one entry for id 1, don't tell
                # the storage about the rest
                return types.PutPhotoResponse(None)

        # we'll use the most recent photo as the "real" one in storage
        self._storage.store_photo(
            request.username, request.photo_id, request.photo_blob
        )
        self._storage.log_operation(request.username, request.encoded_log_entry)
        return types.PutPhotoResponse(None)

    def get_photo_user(self, request: types.GetPhotoRequest) -> types.GetPhotoResponse:
        if not self._storage.check_token(request.username, request.token):
            return types.GetPhotoResponse(types.Errcode.INVALID_TOKEN, None)

        photo = self._storage.load_photo(request.username, request.photo_id)
        if request.photo_id == 1:
            # get the fake per-client photo instead of the real one
            _, photo = self.alternate_log_entries[request.client_id]
        if photo != None:
            return types.GetPhotoResponse(None, photo.photo_blob)
        else:
            return types.GetPhotoResponse(types.Errcode.PHOTO_DOES_NOT_EXIST, None)

    def synchronize(
        self, request: types.SynchronizeRequest
    ) -> types.SynchronizeResponse:
        if not self._storage.check_token(request.username, request.token):
            return types.SynchronizeResponse(types.Errcode.INVALID_TOKEN, None)

        # Check version compatibility
        server_version = self._storage.latest_user_version(request.username)
        if request.min_version_number > server_version + 1:
            return types.SynchronizeResponse(types.Errcode.VERSION_TOO_HIGH, None)

        log = self._storage.user_history(request.username, request.min_version_number)

        # replace the entry with the one for the right client (hacky...)
        new_log = []
        for entry in log:
            if entry in [e for e, _ in self.alternate_log_entries.values()]:
                if request.client_id in self.alternate_log_entries:
                    # if we have an alternate entry for this, replace it.
                    # If this log entry matches an alternate but we have nothing
                    # for this client id, skip this log entry (it should be the most recent)
                    new_log.append(self.alternate_log_entries[request.client_id][0])
            else:
                # in the normal case, just copy the entry
                new_log.append(entry)
        return types.SynchronizeResponse(None, new_log)


@test_case(points=6)
def test_single_photo_fork():
    """
    This tests that the client detects when the log
    diverged between the two clients for a single photo
    and then rejoined. If this goes undetected, the two
    clients will have different photo histories.

    A SynchronizationError should be raised by the time that
    `alice_b` posts a new photo, since at that point it will
    have synchronized `alice_a`s insertion of `photo2` but not
    her insertion of `photo1_a`. It is also valid to raise
    the error before this point.
    """
    pts = 6

    try:
        server = ForkServer()
        alice_a = new_client(server, "alice")
        alice_a.register()
        alice_b = new_authorized_device(server, alice_a)

        alice_a.login()
        photo_blob0 = b"photo0"
        if alice_a.put_photo(photo_blob0) != 0:
            pts -= 1
        if alice_a.put_photo(b"photo1_a") != 1:
            pts -= 1

        alice_b.login()
        if alice_b.put_photo(b"photo1_b") != 1:
            # note both this and the above return 1!
            pts -= 1

        alice_a.login()
        photo_blob2 = b"photo2"
        if alice_a.put_photo(photo_blob2) != 2:
            pts -= 1

        # when alice_b logs in and synchronizes here,
        # they will see alice_a's photo2. However,
        # alice_b has never heard about photo1_a.
        # therefore, alice_b must realize that there
        # is an error here in order to implement the
        # security properties.
        alice_b.login()
        photo_blob3 = b"photo3"
        try:
            alice_b.put_photo(photo_blob3)
            pts = 0
        except errors.SynchronizationError:
            return max(pts, 0)

        # if we got to here, failed to find the error.
        return 0

    except:
        traceback.print_exc()
        return 0

