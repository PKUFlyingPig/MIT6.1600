### security

# confidentiality

from cmath import exp
from enum import Enum
import typing as t
from ag.ag3.impolite_client import ImpoliteClient

from ag.ag3.common import STANDARD_ALBUM
from server.reference_server import InMemoryStorage, ReferenceServer
from server.spec import Server
import common.types as types
import common.errors as errors
import common.crypto as crypto
import common.codec as codec
from ag.common.testing import test_case
from ag.common.mock_http import link_client_server
from ag.common.fixtures import (
    new_client,
    new_registered_client,
    new_device,
    two_friends,
)
from .override_fixtures import three_clients, two_clients

from . import crypto_overrides as co

from client import client

# replace crypto with ones that allow us to track usage
crypto.UserSecret = co.UserSecret
crypto.PublicKeySignature = co.PublicKeySignature
crypto.SymmetricKeyEncryption = co.SymmetricKeyEncryption
crypto.PublicKeyEncryptionAndAuthentication = co.PublicKeyEncryptionAndAuthentication
crypto.generate_symmetric_secret_key = co.generate_symmetric_secret_key
crypto.verify_sign = co.verify_sign


class SaveReqRespServer(ReferenceServer):
    """
    This server behaves just like the reference server,
    but saves request and response for easy access
    """

    def __init__(self):
        self.last_request = None
        self.last_response = None
        self.last_album_upload_request = None
        self.last_album_upload_response = None
        self.last_album_get_request = None
        self.last_album_get_response = None
        super().__init__()

    def register_user(self, request):
        self.last_request = request
        self.last_response = super().register_user(request)
        return self.last_response

    def update_public_profile(self, request):
        self.last_request = request
        self.last_response = super().update_public_profile(request)
        return self.last_response

    def get_friend_public_profile(self, request):
        self.last_request = request
        self.last_response = super().get_friend_public_profile(request)
        return self.last_response

    def upload_album(self, request):
        self.last_request = request
        self.last_album_upload_request = request
        response = super().upload_album(request)
        self.last_response = response
        self.last_album_upload_response = response
        return self.last_response

    def get_album(self, request):
        self.last_request = request
        self.last_album_get_request = request
        response = super().get_album(request)
        self.last_response = response
        self.last_album_get_response = response
        return self.last_response


class ViewStatus(Enum):
    NONE = 1
    SOME = 2
    ALL = 3


def check_view(
    user: client.Client,
    server: Server,
    photos: t.List[bytes],
    view: t.Optional[co.View] = None,
) -> ViewStatus:
    """
    Checks which of the photos in `photos` the `user` can see,
    and returns the corresponding ViewStatus

    Note: the album must have been retrieved before this

    If a view is given in `existing_view`, that one will be used.
    Otherwise, a new view will be created.
    """
    request = server.last_album_get_request
    response = server.last_album_get_response
    if type(request) != types.GetAlbumRequest:
        raise ValueError("Server request type incorrect")
    if request.username != user.username:
        raise ValueError("Server request username incorrect")
    if type(response) != types.GetAlbumResponse:
        raise ValueError("Server response type incorrect")
    if view is None:
        view = co.View(user)
    view.add_obj(response.album)
    overlap = set()
    for p in photos:
        if p in view.available_data:
            overlap.add(p)

    if overlap == set(photos):
        return ViewStatus.ALL
    elif len(overlap) == 0:
        return ViewStatus.NONE
    else:
        return ViewStatus.SOME


def album_contains_all(
    user: client.Client,
    server: Server,
    photos: t.List[bytes],
    album_name: str = "my_album",
    view: t.Optional[co.View] = None,
) -> bool:
    co.current_owner = user.username
    result = user.get_album(album_name)["photos"]
    if set(photos).intersection(set(result)) != set(photos):
        # correctness failed!
        print("\tcorrectness failed! Got", result, "expected", photos)
        return False
    if check_view(user, server, photos, view=view) == ViewStatus.ALL:
        return True
    return False


def album_contains_none(
    user: client.Client,
    server: Server,
    photos: t.List[bytes],
    expect_permission_error: bool = True,
    album_name: str = "my_album",
    view: t.Optional[co.View] = None,
) -> bool:
    """
    Ensures that:
    a) Fetching the album raises an AlbumPermissionError
    b) the contents of the album returned from the server do
        not allow the user to see any of the given photos
    """
    co.current_owner = user.username
    try:
        user.get_album(album_name)["photos"]
    except errors.AlbumPermissionError as e:
        if expect_permission_error:
            if check_view(user, server, photos, view=view) == ViewStatus.NONE:
                return True
        else:
            raise e

    if not expect_permission_error:
        if check_view(user, server, photos, view=view) == ViewStatus.NONE:
            return True
    return False


def new_registered_impolite_client(username: str, server: Server) -> ImpoliteClient:
    co.current_owner = username
    c = ImpoliteClient(username)
    link_client_server(c, server)
    c.register()
    return c


@test_case(points=10, starter_points=0)
def security_add_friend():
    pts = 10
    co.reset()

    co.current_owner = "None"
    server = SaveReqRespServer()
    alice, bob, carlos = three_clients(server)
    alice.add_friend(bob.username, bob.signing_public_key)
    bob.add_friend(alice.username, alice.signing_public_key)
    carlos.add_friend(alice.username, alice.signing_public_key)

    # Create Album
    co.current_owner = "alice"
    alice.create_shared_album("my_album", STANDARD_ALBUM, [])

    # Check that Bob cannot access the photos
    if not album_contains_none(bob, server, STANDARD_ALBUM):
        print(f"\t (1) user 'bob' has access to photo blob in unshared album!")
        return 0

    # Add Bob to the album
    co.current_owner = "alice"
    alice.add_friend_to_album("my_album", bob.username)

    # Check that Bob can access all the photos
    if not album_contains_all(bob, server, STANDARD_ALBUM):
        print(f"\t (2) user 'bob' does not have access to photo blob in shared album!")
        return 0

    # Check that Carlos cannot access any photos
    if not album_contains_none(carlos, server, STANDARD_ALBUM):
        print(f"\t (3) user 'carlos' has access to photo blob in unshared album!")
        return 0

    return pts


@test_case(points=10, starter_points=0)
def security_non_friend_cannot_see_new_photos():
    pts = 10
    co.reset()

    co.current_owner = "None"
    server = SaveReqRespServer()
    alice, bob, carlos = three_clients(server)
    alice.add_friend(bob.username, bob.signing_public_key)
    alice.add_friend(carlos.username, carlos.signing_public_key)
    bob.add_friend(alice.username, alice.signing_public_key)
    carlos.add_friend(alice.username, alice.signing_public_key)

    # Create Album
    co.current_owner = alice.username
    album = STANDARD_ALBUM.copy()
    alice.create_shared_album("my_album", album, ["bob"])

    # Test that Bob can access the photos
    if not album_contains_all(bob, server, album):
        print("\t (1) bob cannot see photos in album that he belongs to")
        return 0

    # Add a photo to the album
    co.current_owner = "bob"
    new_photo = b"PHOOBOB"
    album.append(new_photo)
    bob.add_photo_to_album("my_album", new_photo)

    # Test that Carlos cannot access any photo
    if not album_contains_none(carlos, server, album):
        print("\t (2) Carlos could access photos in album he is not part of")
        return 0

    # Test that Bob can access the photos
    if not album_contains_all(bob, server, album):
        print("\t (3) bob cannot see photos in album that he belongs to")
        return 0

    # Test that Carlos cannot access any photo
    if not album_contains_none(carlos, server, album):
        print("\t (4) Carlos could access photos in album he is not part of")
        return 0

    # Test that Alice can access the photos
    if not album_contains_all(alice, server, album):
        print("\t (5) alice cannot see photos in album that she belongs to")
        return 0

    # Test that Carlos cannot access any photo
    if not album_contains_none(carlos, server, album):
        print("\t (6) Carlos could access photos in album he is not part of")
        return 0

    # Add a photo to the album
    co.current_owner = "alice"
    new_photo = b"PHOOOOO"
    album.append(new_photo)
    alice.add_photo_to_album("my_album", new_photo)

    # Test that Carlos cannot access any photo
    if not album_contains_none(carlos, server, album):
        print("\t (7) Carlos could access photos in album he is not part of")
        return 0

    return pts


@test_case(points=10, starter_points=0)
def security_removed_friend_cannot_see_new_request():
    pts = 10
    co.reset()

    co.current_owner = "None"
    server = SaveReqRespServer()
    alice, bob, carlos = three_clients(server)
    alice.add_friend(bob.username, bob.signing_public_key)
    alice.add_friend(carlos.username, carlos.signing_public_key)
    bob.add_friend(alice.username, alice.signing_public_key)
    carlos.add_friend(alice.username, alice.signing_public_key)

    carlos_view = co.View(carlos)

    # Create Album
    co.current_owner = alice.username
    alice.create_shared_album("my_album", STANDARD_ALBUM, ["bob", "carlos"])

    # Test that Carlos can access the photos
    if not album_contains_all(carlos, server, STANDARD_ALBUM, view=carlos_view):
        print("\t (1) carlos cannot view all photos in shared album")
        return 0

    # Remove Carlos
    co.current_owner = "alice"
    alice.remove_friend_from_album("my_album", carlos.username)

    # clear carlos's available data so we only consider new data
    carlos_view.available_data = set()

    # Test that Carlos cannot access any photo
    if not album_contains_none(carlos, server, STANDARD_ALBUM, view=carlos_view):
        print("\t (2) carlos can view photos after removal from album")
        return 0

    # Test that Bob can access the photos
    if not album_contains_all(bob, server, STANDARD_ALBUM):
        print("\t (3) bob cannot see photos after carlos's removal")
        return 0

    return pts


@test_case(points=10, starter_points=0)
def security_removed_friend_cannot_see_new_photo():
    pts = 10
    co.reset()

    co.current_owner = "None"
    server = SaveReqRespServer()
    alice, bob, carlos = three_clients(server)
    alice.add_friend(bob.username, bob.signing_public_key)
    alice.add_friend(carlos.username, carlos.signing_public_key)
    bob.add_friend(alice.username, alice.signing_public_key)
    carlos.add_friend(alice.username, alice.signing_public_key)
    carlos_view = co.View(carlos)

    # Create Album
    co.current_owner = alice.username
    alice.create_shared_album("my_album", STANDARD_ALBUM, ["bob", "carlos"])

    # Test that Bob can access the photos
    if not album_contains_all(bob, server, STANDARD_ALBUM):
        print("\t (1) bob cannot see photos in album that he belongs to")
        return 0

    # Test that Carlos can access the photos
    if not album_contains_all(carlos, server, STANDARD_ALBUM, view=carlos_view):
        print("\t (2) carlos cannot see photos in album that he belongs to")
        return 0

    # Remove Cedric from the album
    co.current_owner = alice.username
    alice.remove_friend_from_album("my_album", "carlos")

    # Add a new photo
    co.current_owner = bob.username
    new_photo = b"PHOTOBOB"
    bob.add_photo_to_album("my_album", new_photo)

    # Test that Carlos cannot see the new photo
    if not album_contains_none(carlos, server, [new_photo], view=carlos_view):
        print("\t (3) carlos could view new photo (1) added after his removal")
        return 0

    # Test Alice can see the new photo
    if not album_contains_all(alice, server, [new_photo]):
        print(
            "\t (4) alice could not view new photo added by bob after carlos's removal"
        )
        return 0

    # Add a new photo
    co.current_owner = "alice"
    new_photo = b"PHOOOOO"
    alice.add_photo_to_album("my_album", new_photo)

    # Test that Carlos cannot see the new photo
    if not album_contains_none(carlos, server, [new_photo], view=carlos_view):
        print("\t (5) carlos could view new photo (1) added after his removal")
        return 0

    # Test Bob can see the new photo
    if not album_contains_all(bob, server, [new_photo]):
        print(
            "\t (6) bob could not view new photo added by alice after carlos's removal"
        )
        return 0

    return pts


@test_case(points=10, starter_points=0)
def security_user_adds_self_to_album():
    pts = 10
    co.reset()

    co.current_owner = "None"
    server = SaveReqRespServer()
    alice, bob = two_clients(server)
    carlos = new_registered_impolite_client("carlos", server)

    # Create Album
    co.current_owner = alice.username
    alice.create_shared_album("my_album", STANDARD_ALBUM, [])

    # We verify in prior test case that bob cannot access any photos

    # Carlos adds himself
    co.current_owner = "carlos"
    carlos.add_friend_to_album("my_album", "carlos")

    # Alice adds bob
    co.current_owner = "alice"
    alice.add_friend(bob.username, bob.signing_public_key)
    bob.add_friend(alice.username, alice.signing_public_key)
    alice.add_friend_to_album("my_album", "bob")

    # Check that Bob can access the photos
    if not album_contains_all(bob, server, STANDARD_ALBUM):
        print(f"\t (1) user 'bob' does not have access to photo blob in shared album!")
        return 0

    # Check that Carlos cannot access any photos
    if not album_contains_none(carlos, server, STANDARD_ALBUM, False):
        print(f"\t (2) user 'carlos' has access to photo blob in unshared album!")
        return 0

    return pts


@test_case(points=10, starter_points=0)
def security_user_adds_self_to_album_new_photo():
    pts = 10
    co.reset()

    co.current_owner = "None"
    server = SaveReqRespServer()
    alice, bob = two_clients(server)
    carlos = new_registered_impolite_client("carlos", server)

    # Create Album
    co.current_owner = alice.username
    alice.create_shared_album("my_album", STANDARD_ALBUM, [])

    # We verify in prior test case that bob cannot access any photos

    # Carlos adds himself
    co.current_owner = "carlos"
    carlos.add_friend_to_album("my_album", "carlos")

    # Alice adds bob
    co.current_owner = "alice"
    alice.add_friend(bob.username, bob.signing_public_key)
    bob.add_friend(alice.username, alice.signing_public_key)
    alice.add_friend_to_album("my_album", "bob")

    # Check that Bob can access the photos
    if not album_contains_all(bob, server, STANDARD_ALBUM):
        print(f"\t (1) user 'bob' does not have access to photo blob in shared album!")
        return 0

    # Check that Carlos cannot access any photos
    if not album_contains_none(carlos, server, STANDARD_ALBUM, False):
        print(f"\t (2) user 'carlos' has access to photo blob in unshared album!")
        return 0

    return pts

