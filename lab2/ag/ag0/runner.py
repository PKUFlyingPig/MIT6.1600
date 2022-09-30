#!/usr/bin/env python3

import traceback
from ag.common.mock_http import link_client_server
from ag.common.testing import test_case

from server.reference_server import *
from common.crypto import *
import common.types as types
import common.errors as errors

from client import client

# these inherit from ReferenceServer and override any methods that they need to change. This maintains compatability
# with the rpc.
class TestServer(ReferenceServer):
    def __init__(self):
        self.last_request = None
        self.last_response = None
        self._real_server = ReferenceServer()

    def register_user(self, request):
        self.last_request = request
        self.last_response = self._real_server.register_user(request)
        return self.last_response

    def update_public_profile(self, request):
        self.last_request = request
        self.last_response = self._real_server.update_public_profile(request)
        return self.last_response

    def get_friend_public_profile(self, request):
        self.last_request = request
        self.last_response = self._real_server.get_friend_public_profile(request)
        return self.last_response


class ErrorServer_0:
    def __init__(self):
        self._real_server = ReferenceServer()

    def register_user(self, request):
        return self._real_server.register_user(request)

    def update_public_profile(self, request):
        return types.UpdatePublicProfileResponse(types.Errcode.INVALID_TOKEN)


class ErrorServer_1:
    def __init__(self):
        self._real_server = ReferenceServer()

    def register_user(self, request):
        return self._real_server.register_user(request)

    def update_public_profile(self, request):
        return types.UpdatePublicProfileResponse(types.Errcode.UNKNOWN)


class ErrorServer_2:
    def __init__(self):
        self._real_server = ReferenceServer()

    def register_user(self, request):
        return self._real_server.register_user(request)

    def update_public_profile(self, request):
        return self._real_server.update_public_profile(request)

    def get_friend_public_profile(self, request):
        return types.GetFriendPublicProfileResponse(types.Errcode.INVALID_TOKEN, None)


class ErrorServer_3:
    def __init__(self):
        self._real_server = ReferenceServer()

    def register_user(self, request):
        return self._real_server.register_user(request)

    def update_public_profile(self, request):
        return self._real_server.update_public_profile(request)

    def get_friend_public_profile(self, request):
        return types.GetFriendPublicProfileResponse(types.Errcode.UNKNOWN, None)


@test_case(points=1)
def test_correct_behavior_1():
    pts = 1
    try:
        server = ReferenceServer()
        alice = client.Client("alice", "")
        link_client_server(alice, server)

        alice.register()
        infos = {
            "bio": "I like computer security and cryptography",
            "location": "MIT",
            "camera": "mobile phone",
        }
        alice.update_public_profile(infos)
    except Exception as e:
        traceback.print_exc()
        return 0
    return pts


@test_case(points=6)
def test_correct_behavior_2():
    pts = 0
    try:
        server = TestServer()
        alice = client.Client("alice", "")
        link_client_server(alice, server)

        alice.register()
        token = server.last_response.token
        infos = {
            "bio": "I like computer security and cryptography",
            "location": "MIT",
            "camera": "mobile phone",
        }
        alice.update_public_profile(infos)
        request = server.last_request
        if type(request) == types.UpdatePublicProfileRequest:
            pts += 1
        else:
            return pts
        if request.username == "alice":
            pts += 1
        else:
            return pts
        if request.token == token:
            pts += 1
        else:
            return pts
        if request.public_profile.username == "alice":
            pts += 1
        else:
            return pts
        if request.public_profile.profile == infos:
            pts += 2
        else:
            return pts
    except Exception as e:
        traceback.print_exc()
        return 0
    return pts


@test_case(points=2)
def test_correct_behavior_3():
    pts = 2
    try:
        server = TestServer()
        alice = client.Client("alice", "")
        link_client_server(alice, server)

        alice.register()
        token = server.last_response.token
        infos = {
            "bio": "I like computer security and cryptography",
            "location": "MIT",
            "camera": "mobile phone",
        }
        alice.update_public_profile(infos)
        received_pp = server.get_friend_public_profile(
            types.GetFriendPublicProfileRequest(
                client_id=alice._client_id,
                username="alice",
                token=token,
                friend_username="alice",
            )
        ).public_profile
        new_infos = received_pp.profile
        if new_infos != infos:
            pts = 0
    except Exception as e:
        traceback.print_exc()
        return 0
    return pts


@test_case(points=4)
def test_correct_behavior_4():
    pts = 0
    try:
        server = TestServer()
        alice = client.Client("alice", "")
        link_client_server(alice, server)
        bob = client.Client("bob", server)
        link_client_server(bob, server)

        alice.register()
        infos = {
            "bio": "I like computer security and cryptography",
            "location": "MIT",
            "camera": "mobile phone",
        }
        alice.update_public_profile(infos)
        bob.register()
        token = server.last_response.token
        bob.get_friend_public_profile("alice")
        request = server.last_request
        if type(request) == types.GetFriendPublicProfileRequest:
            pts += 1
        else:
            return pts
        if request.username == "bob":
            pts += 1
        else:
            return pts
        if request.token == token:
            pts += 1
        else:
            return pts
        if request.friend_username == "alice":
            pts += 1
        else:
            return pts
    except Exception as e:
        traceback.print_exc()
        return 0
    return pts


@test_case(points=2)
def test_correct_behavior_5():
    pts = 2
    try:
        server = ReferenceServer()
        alice = client.Client("alice", "")
        link_client_server(alice, server)
        bob = client.Client("bob", server)
        link_client_server(bob, server)

        alice.register()
        infos = {
            "bio": "I like computer security and cryptography",
            "location": "MIT",
            "camera": "mobile phone",
        }
        alice.update_public_profile(infos)
        bob.register()
        received_pp = bob.get_friend_public_profile("alice")
        new_infos = received_pp.profile
        if new_infos != infos:
            pts = 0
    except Exception as e:
        traceback.print_exc()
        return 0
    return pts

