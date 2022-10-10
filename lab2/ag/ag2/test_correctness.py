from re import I
import typing as t
from common.errors import SynchronizationError

from server.reference_server import InMemoryStorage, ReferenceServer
from server.spec import Server
import common.types as types
import common.errors as errors
from ag.common.testing import test_case
from ag.common.mock_http import link_client_server
from ag.common.fixtures import two_clients, new_device

from client import client


@test_case(points=1, starter_points=1)
def view_friend_photos():
    pts = 1

    server = ReferenceServer()

    # create two clients
    alice, bob = two_clients(server)
    bob.put_photo(b"bob_another_photo")

    # alice can view bob's photos
    alice.add_friend("bob", bob.public_key)
    bob_photos = alice.get_friend_photos("bob")

    expected = [b"bob_photo_0", b"bob_another_photo"]
    if not bob_photos == expected:
        print(f"Incorrect photos returned! Expected {expected}, got {bob_photos}")
        return 0

    return pts


@test_case(points=1, starter_points=1)
def update_friend_photos():
    pts = 1

    server = ReferenceServer()

    # create two clients
    alice, bob = two_clients(server)
    bob.put_photo(b"bob_another_photo")

    # alice can view bob's photos
    alice.add_friend("bob", bob.public_key)
    bob_photos = alice.get_friend_photos("bob")

    expected = [b"bob_photo_0", b"bob_another_photo"]
    if not bob_photos == expected:
        print(f"Incorrect photos returned! Expected {expected}, got {bob_photos}")
        return 0

    # alice updates correctly after bob adds a photo
    bob.put_photo(b"bob_third_photo")
    bob_photos = alice.get_friend_photos("bob")
    expected = [b"bob_photo_0", b"bob_another_photo", b"bob_third_photo"]
    if not bob_photos == expected:
        print(f"Incorrect photos returned! Expected {expected}, got {bob_photos}")
        return 0

    return pts


@test_case(points=1, starter_points=1)
def dual_device_friend():
    pts = 1
    server = ReferenceServer()
    alice, bob = two_clients(server)

    bob_2 = new_device(server, bob)
    bob.invite_device(bob_2.public_key)
    bob_2.login()
    bob_2.accept_invite(bob.public_key)

    bob_2.put_photo(b"bob_2_photo")

    bob.login()
    bob.put_photo(b"bob_photo_2")

    # alice adds bob's original device as a friend,
    # and should then return the photos pushed by both devices
    alice.add_friend("bob", bob.public_key)
    bob_photos = alice.get_friend_photos("bob")

    if not bob_photos == [b"bob_photo_0", b"bob_2_photo", b"bob_photo_2"]:
        return 0
    return pts


@test_case(points=1, starter_points=1)
def dual_device_friend_latest_key():
    """
    Identical to dual_device_friend, but alice adds bob
    as a user using the key of his second device instead of his first.
    """
    pts = 1
    server = ReferenceServer()
    alice, bob = two_clients(server)

    bob_2 = new_device(server, bob)
    bob.invite_device(bob_2.public_key)
    bob_2.login()
    bob_2.accept_invite(bob.public_key)

    bob_2.put_photo(b"bob_2_photo")

    bob.login()
    bob.put_photo(b"bob_photo_2")

    # alice adds bob's original device as a friend,
    # and should then return the photos pushed by both devices
    alice.add_friend("bob", bob_2.public_key)
    bob_photos = alice.get_friend_photos("bob")

    if not bob_photos == [b"bob_photo_0", b"bob_2_photo", b"bob_photo_2"]:
        return 0
    return pts


@test_case(points=2, starter_points=2)
def triple_device_friend():
    """
    In this test, bob has three devices and alice tries to add
    bob using the second device's public key.
    """
    pts = 2
    server = ReferenceServer()
    alice, bob = two_clients(server)

    # add device 2
    bob_2 = new_device(server, bob)
    bob.login()
    bob.invite_device(bob_2.public_key)
    bob_2.login()
    bob_2.accept_invite(bob.public_key)
    bob_2.put_photo(b"bob_2_photo_0")

    # add device 3
    bob_3 = new_device(server, bob)
    bob.login()
    bob.invite_device(bob_3.public_key)
    bob_3.login()
    bob_3.accept_invite(bob.public_key)
    bob_3.put_photo(b"bob_3_photo_0")

    # put one more photo from device 1
    bob.login()
    bob.put_photo(b"bob_photo_1")

    alice.add_friend("bob", bob_2.public_key)
    bob_photos = alice.get_friend_photos("bob")

    expected = [b"bob_photo_0", b"bob_2_photo_0", b"bob_3_photo_0", b"bob_photo_1"]
    if not bob_photos == expected:
        print(f"Incorrect photos returned! Expected {expected}, got {bob_photos}")
        return 0

    return pts


@test_case(points=2, starter_points=2)
def triple_device_chained_invite():
    """
    This test case is identical to `triple_device_friend`, except
    instead of the first "bob" device inviting both other devices,
    bob_2 invites bob_3. This should behave equivalently.
    """
    pts = 2
    server = ReferenceServer()
    alice, bob = two_clients(server)

    # add device 2
    bob_2 = new_device(server, bob)
    bob.login()
    bob.invite_device(bob_2.public_key)
    bob_2.login()
    bob_2.accept_invite(bob.public_key)
    bob_2.put_photo(b"bob_2_photo_0")

    # add device 3
    bob_3 = new_device(server, bob)
    bob_2.invite_device(bob_3.public_key)
    bob_3.login()
    bob_3.accept_invite(bob_2.public_key)
    bob_3.put_photo(b"bob_3_photo_0")

    # put one more photo from device 1
    bob.login()
    bob.put_photo(b"bob_photo_1")

    # and one more from device 2
    bob_2.login()
    bob_2.put_photo(b"bob_2_photo_1")

    alice.add_friend("bob", bob_2.public_key)
    bob_photos = alice.get_friend_photos("bob")

    expected = [
        b"bob_photo_0",
        b"bob_2_photo_0",
        b"bob_3_photo_0",
        b"bob_photo_1",
        b"bob_2_photo_1",
    ]
    if not bob_photos == expected:
        print(f"Incorrect photos returned! Expected {expected}, got {bob_photos}")
        return 0

    return pts


@test_case(points=2, starter_points=2)
def revoke_device():
    """
    In this test case, bob adds a device bob_2 which uploads one photo.
    Then, bob revokes bob_2. This should not cause any errors, and both
    bob's and bob_2's uploaded photos should be returned (since bob_2 was
    not revoked at the time of upload)
    """
    pts = 2

    server = ReferenceServer()
    alice, bob = two_clients(server)

    bob_2 = new_device(server, bob)
    bob.invite_device(bob_2.public_key)
    bob_2.login()
    bob_2.accept_invite(bob.public_key)

    bob_2.login()
    bob_2.put_photo(b"bob_2_approved")

    # revoke device 2
    bob.login()
    bob.revoke_device(bob_2.public_key)
    bob.put_photo(b"bob_photo_1")

    alice.add_friend("bob", bob.public_key)

    expected = [b"bob_photo_0", b"bob_2_approved", b"bob_photo_1"]
    bob_photos = alice.get_friend_photos("bob")
    if not bob_photos == expected:
        print(f"Incorrect photos returned! Expected {expected}, got {bob_photos}")
        return 0

    return pts

