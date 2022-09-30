import typing as t
from common.types import SynchronizeFriendRequest

from server.reference_server import ReferenceServer
import common.errors as errors
from ag.common.testing import test_case
from ag.common.fixtures import two_clients, new_device, new_authorized_device

from client import client


@test_case(points=4)
def server_suppresses_revocation():
    """
    In this test case, the server does not tell
    anyone about the revocation of device B.
    """
    pts = 4

    server = ReferenceServer()

    # create user alice with one device and bob with 3 devices
    alice, bob = two_clients(server)
    bob_2 = new_authorized_device(server, bob)
    bob_3 = new_authorized_device(server, bob)
    bob_2.login()
    bob_2.put_photo(b"bob_2_photo_0")
    bob_3.login()
    bob_3.put_photo(b"bob_3_photo_0")

    # at this point, an attacker compromises bob_2
    # so bob revokes it.

    # first, we store the state of the log as it is _before_ bob revokes bob_2
    server_log_pre_revoke = server._storage.userbase[bob.username].history.copy()
    bob.login()
    bob.revoke_device(bob_2.public_key)
    # after the revocation, we put back the pre-revocation log, suppressing the revocation entry
    server._storage.userbase[bob.username].history = server_log_pre_revoke

    # now, bob has revoked the device but the
    # server suppressed the revocation entry(ies)
    # however, a friend device has no way of knowing about this
    alice.login()
    alice.add_friend(bob.username, bob.public_key)
    expected = [b"bob_photo_0", b"bob_2_photo_0", b"bob_3_photo_0"]
    bob_photos = alice.get_friend_photos(bob.username)
    if not bob_photos == expected:
        # listing bob's photos should be successful (everything is valid from alice's perspective)
        print(f"Incorrect photos returned! Expected {expected}, got {bob_photos}")
        return 0

    # since the revocation message was suppressed, bob_2 can even
    # post another photo and there is nothing we can do to detect it
    bob_2.login()
    bob_2.put_photo(b"evil_bad_terrible_photo")
    expected = [
        b"bob_photo_0",
        b"bob_2_photo_0",
        b"bob_3_photo_0",
        b"evil_bad_terrible_photo",
    ]
    bob_photos = alice.get_friend_photos(bob.username)
    if not bob_photos == expected:
        # listing bob's photos should be successful (everything is valid from alice's perspective)
        print(f"Incorrect photos returned! Expected {expected}, got {bob_photos}")
        return 0

    # however, if _bob_ adds another entry to the log, then alice
    # should realize that something is wrong.
    # note: it may seem like bob may also realize that something is wrong here, since it will
    # synchronize an entry from a user that it knows to be revoked (bob_2). However, bob is 1
    # log entry ahead of the rest of the clients and thus will _not see_ evil_bad_terrible_photo.
    bob.login()
    bob.put_photo(b"regular_old_photo")

    try:
        alice.get_friend_photos(bob.username)
    except errors.SynchronizationError as e:
        return pts

    print("did not catch suppressed revocation!")
    return 0


@test_case(points=4)
def server_replays_approval():
    """
    The server replays the approval of device B after
    device A revokes it.
    """
    pts = 4

    server = ReferenceServer()

    # create user alice with one device and bob with 3 devices
    alice, bob = two_clients(server)
    bob_2 = new_device(server, bob)

    # record the state of the log before and after bob_2's approval
    server_log_pre_approve = server._storage.userbase[bob.username].history.copy()
    bob.login()
    bob.invite_device(bob_2.public_key)
    server_log_post_approve = server._storage.userbase[bob.username].history.copy()

    # find the difference between the log to get the approval entry(ies)
    approval_entries = server_log_post_approve[len(server_log_pre_approve) :].copy()

    # bob_2 behaves normally
    bob_2.login()
    bob_2.accept_invite(bob.public_key)
    bob_2.put_photo(b"bob_2_photo_0")

    # at this point, an attacker compromises bob_2
    # so bob revokes it.
    bob.login()
    bob.revoke_device(bob_2.public_key)
    bob.put_photo(b"bob_happy_that_he_revoked_bob_2_photo")

    # the server saves the current index -- it will insert the log entries to approve bob_2 later
    # (we can't insert them now or else bob_2 may fail to synchronize)
    reapproval_i = len(server._storage.userbase[bob.username].history)

    # and bob_2 pretends that he got re-invited for real
    bob_2.login()
    bob_2.accept_invite(bob.public_key)
    bob_2.put_photo(b"bob_2_evil_laugh")

    # now, the server inserts the approval log entries
    server._storage.userbase[bob.username].history[
        reapproval_i:reapproval_i
    ] = approval_entries

    # alice tries to list bob's photos
    # she should realize that the second approval was faked
    alice.add_friend("bob", bob.public_key)
    try:
        alice.get_friend_photos("bob")
    except errors.SynchronizationError:
        return pts
    return 0

