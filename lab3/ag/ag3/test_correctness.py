#!/usr/bin/env python3

import traceback
import random

from server.reference_server import InMemoryStorage, ReferenceServer
from server.spec import Server
import common.types as types
import common.errors as errors
from ag.common.testing import test_case
from ag.common.mock_http import link_client_server
from ag.common.fixtures import (
    new_client,
    new_registered_client,
    three_clients,
    two_clients,
    new_device,
    two_friends,
)
from ag.ag3.common import STANDARD_ALBUM

from client import client

### correctness
@test_case(points=1, starter_points=1)
def correctness_create_album():
    pts = 1
    server = ReferenceServer()
    alice, bob = two_clients(server)
    alice.add_friend(bob.username, bob.signing_public_key)
    alice.create_shared_album("my_album", STANDARD_ALBUM, ["bob"])
    return pts


@test_case(points=1, starter_points=1)
def correctness_get_album():
    pts = 1
    server = ReferenceServer()
    alice, bob = two_friends(server)
    alice.create_shared_album("my_album", STANDARD_ALBUM, ["bob"])
    photos_received = bob.get_album("my_album")["photos"]
    expected = STANDARD_ALBUM
    if photos_received != expected:
        print(
            f"\tReceived incorrect album contents! Expected {expected}, got {photos_received}"
        )
        return 0
    return 1


@test_case(points=1, starter_points=1)
def correctness_add_friend():
    pts = 1
    server = ReferenceServer()
    alice, bob = two_friends(server)

    alice.create_shared_album("my_album", STANDARD_ALBUM, [])
    try:
        photos_received = bob.get_album("my_album")["photos"]
        pts = 0
    except errors.AlbumPermissionError:
        alice.add_friend_to_album("my_album", "bob")
        photos_received = bob.get_album("my_album")["photos"]
        expected = STANDARD_ALBUM
        if photos_received != expected:
            print(
                f"\tReceived incorrect album contents! Expected {expected}, got {photos_received}"
            )
            return 0
    return pts


@test_case(points=1, starter_points=1)
def correctness_remove_friend():
    pts = 1
    server = ReferenceServer()
    alice, bob = two_friends(server)

    alice.create_shared_album("my_album", STANDARD_ALBUM, ["bob"])
    photos_received = bob.get_album("my_album")["photos"]
    expected = STANDARD_ALBUM
    if photos_received != expected:
        print(
            f"\tReceived incorrect album contents! Expected {expected}, got {photos_received}"
        )
        return 0
    alice.remove_friend_from_album("my_album", "bob")
    try:
        photos_received = bob.get_album("my_album")["photos"]
        return 0
    except errors.AlbumPermissionError:
        pass
    return pts


@test_case(points=1, starter_points=1)
def correctness_add_photo():
    pts = 1
    server = ReferenceServer()
    alice, bob, carlos = three_clients(server)
    alice.add_friend(bob.username, bob.signing_public_key)
    alice.add_friend(carlos.username, carlos.signing_public_key)
    bob.add_friend(alice.username, alice.signing_public_key)
    carlos.add_friend(alice.username, alice.signing_public_key)
    alice.create_shared_album("my_album", STANDARD_ALBUM, ["bob", "carlos"])
    photos_received = bob.get_album("my_album")["photos"]
    expected = STANDARD_ALBUM.copy()
    if photos_received != expected:
        print(
            f"\tReceived incorrect album (1) contents! Expected {expected}, got {photos_received}"
        )
        return 0
    new_photo = b"photo_new"
    bob.add_photo_to_album("my_album", new_photo)
    photos_received = carlos.get_album("my_album")["photos"]
    expected.append(new_photo)
    if photos_received != expected:
        print(
            f"\tReceived incorrect album (2) contents! Expected {expected}, got {photos_received}"
        )
        return 0
    photos_received = alice.get_album("my_album")["photos"]
    if photos_received != expected:
        print(
            f"\tReceived incorrect album (2) contents! Expected {expected}, got {photos_received}"
        )
        return 0
    return pts


@test_case(points=1, starter_points=1)
def correctness_basic_workflow():
    if check_basic_workflow():
        return 1
    return 0


def check_basic_workflow() -> bool:
    """
    Creates a new album and performs some basic operations:

    - Creates album shared with bob
    - Carlos attempts to view album, check that he cannot
    - Add carlos to album and verify that he can now see photos
    - Bob adds a photo to the album
    - Carlos is removed from the album
    """
    server = ReferenceServer()

    alice, bob, carlos = three_clients(server)
    alice.add_friend(bob.username, bob.signing_public_key)
    bob.add_friend(alice.username, alice.signing_public_key)
    carlos.add_friend(alice.username, alice.signing_public_key)

    alice.create_shared_album("my_album", STANDARD_ALBUM, [bob.username])
    alice.get_album("my_album")
    photos_received = bob.get_album("my_album")["photos"]
    expected = STANDARD_ALBUM.copy()
    if photos_received != expected:
        print(
            f"\tReceived incorrect album (basic 1) contents! Expected {expected}, got {photos_received}"
        )
        return False

    try:
        photos_received = carlos.get_album("my_album")["photos"]
        return False
    except errors.AlbumPermissionError:
        alice.add_friend(carlos.username, carlos.signing_public_key)
        alice.add_friend_to_album("my_album", carlos.username)
        photos_received = bob.get_album("my_album")["photos"]
        if photos_received != expected:
            print(
                f"\tReceived incorrect album (basic 2) contents! Expected {expected}, got {photos_received}"
            )
            return False

    photos_received = carlos.get_album("my_album")["photos"]
    if photos_received != expected:
        print(
            f"\tReceived incorrect album (basic 3) contents! Expected {expected}, got {photos_received}"
        )
        return False
    photos_received = alice.get_album("my_album")["photos"]
    if photos_received != expected:
        print(
            f"\tReceived incorrect album (basic 4) contents! Expected {expected}, got {photos_received}"
        )
        return False

    new_photo = b"photo_bob"
    bob.add_photo_to_album("my_album", new_photo)
    photos_received = carlos.get_album("my_album")["photos"]
    expected.append(new_photo)
    if photos_received != expected:
        print(
            f"\tReceived incorrect album (basic 5) contents! Expected {expected}, got {photos_received}"
        )
        return False

    photos_received = alice.get_album("my_album")["photos"]
    if not photos_received == expected:
        print(
            f"\tReceived incorrect album (basic 6) contents! Expected {expected}, got {photos_received}"
        )
        return False

    alice.remove_friend_from_album("my_album", "carlos")
    try:
        photos_received = carlos.get_album("my_album")["photos"]
        print(
            f"\tReceived incorrect album (basic 7) contents! Expected {expected}, got {photos_received}"
        )
        return False
    except errors.AlbumPermissionError:
        pass
    return True

