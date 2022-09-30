import typing as t

from server.reference_server import ReferenceServer
import common.errors as errors
from ag.common.testing import test_case
from ag.common.fixtures import two_clients, new_device

from client import client


@test_case(points=4)
def other_device_invalid():
    pts = 4

    server = ReferenceServer()
    alice, bob = two_clients(server)

    alice.add_friend("bob", bob.public_key)
    expected = [b"bob_photo_0"]
    bob_photos = alice.get_friend_photos("bob")
    if not bob_photos == expected:
        print(f"Incorrect photos returned! Expected {expected}, got {bob_photos}")
        return 0

    # create a new device but never invite it
    bob_2 = new_device(server, bob)
    bob_2.login()
    bob_2.accept_invite(bob.public_key)  # accepting nonexistent invite
    bob_2.put_photo(b"bob2_unauthorized_photo")

    try:
        bob_photos = alice.get_friend_photos("bob")
    except errors.SynchronizationError:
        return pts

    return 0


@test_case(points=4)
def revoked_device_puts_photo():
    pts = 4

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

    # device 2 tries to put another photo (despite being revoked)
    bob_2.login()
    bob_2.put_photo(b"bob_2_revoked")

    alice.add_friend("bob", bob.public_key)
    try:
        bob_photos = alice.get_friend_photos("bob")
    except errors.SynchronizationError:
        return pts

    return 0


@test_case(points=2)
def unauthorized_device_revokes_device():
    """
    In this case, a device that claims to be bob's but
    was never added tries to revoke one of bob's real devices.
    Alice should notice this and raise a SynchronizationError.
    """
    pts = 2

    server = ReferenceServer()
    alice, bob = two_clients(server)

    bob_2 = new_device(server, bob)
    bob.invite_device(bob_2.public_key)
    bob_2.login()
    bob_2.accept_invite(bob.public_key)

    bob_2.login()
    bob_2.put_photo(b"bob_2_photo_0")

    bob_evil = new_device(server, bob)
    bob_evil.login()
    bob_evil.accept_invite(bob_2.public_key)
    bob_evil.revoke_device(bob_2.public_key)

    # alice should notice that bob_evil illegally revoked
    alice.add_friend("bob", bob.public_key)
    try:
        bob_photos = alice.get_friend_photos("bob")
    except errors.SynchronizationError:
        return pts
    return 0


@test_case(points=2)
def revoked_device_adds_itself():
    pts = 2

    server = ReferenceServer()
    alice, bob = two_clients(server)

    bob_2 = new_device(server, bob)
    bob.invite_device(bob_2.public_key)
    bob_2.login()
    bob_2.accept_invite(bob.public_key)

    # revoke device 2
    bob.login()
    bob.revoke_device(bob_2.public_key)

    # device 2 tries to put another photo (despite being revoked)
    bob_2.login()
    bob_2.invite_device(bob_2.public_key)
    bob_2.accept_invite(bob_2.public_key)

    alice.add_friend("bob", bob.public_key)
    try:
        bob_photos = alice.get_friend_photos("bob")
    except errors.SynchronizationError:
        return pts

    return 0


# TODO: device A adds then revokes device B, device B (or the server) tries to replay the approval from device A, then device B tries to add new photos.

