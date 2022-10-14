#!/usr/bin/env python3

"""
client holds the lab client.
"""

import copy
import typing as t
import uuid

from server.reference_server import *
from client.log_entry import *
import common.crypto as crypto
import common.types as types
import common.codec as codec
import common.errors as errors
import requests

# imported for doctests, unneeded otherwise
from ag.common.mock_http import (
    link_client_server,
)  

@dataclass
class FriendInfo:
    trusted_signing_keys: t.Set[bytes]
    photos: t.List[bytes]
    last_log_number: int


class Client:
    """The client for the photo-sharing application.

    A client can query a remote server for the list of a user's photos
    as well as the photos themselves.  A client can also add photos on
    behalf of that user.

    A client retains data required to authenticate a user's device
    both to a remote server and to other devices.  To authenticate to
    the remote server, the client presents a username and auth_secret,
    while to authenticate to other devices, the client tags
    updates with an authenticator over the history of all updates.  To
    verify the authenticity of an update, clients check the
    authenticator using a shared symmetric key.
    """

    # maps response RPC name to the corresponding type
    RESPONSE_MAPPINGS: t.Dict[str, types.RpcObject] = {
        "RegisterResponse": types.RegisterResponse,
        "LoginResponse": types.LoginResponse,
        "UpdatePublicProfileResponse": types.UpdatePublicProfileResponse,
        "GetFriendPublicProfileResponse": types.GetFriendPublicProfileResponse,
        "PutPhotoResponse": types.PutPhotoResponse,
        "GetPhotoResponse": types.GetPhotoResponse,
        "PushLogEntryResponse": types.PushLogEntryResponse,
        "SynchronizeResponse": types.SynchronizeResponse,
        "SynchronizeFriendResponse": types.SynchronizeFriendResponse,
        "GetAlbumResponse": types.GetAlbumResponse,
        "UploadAlbumResponse": types.UploadAlbumResponse,
    }

    def __init__(
        self,
        username: str,
        remote_url: t.Optional[str] = None,
        user_secret: t.Optional[bytes] = None,
    ) -> None:
        """Initialize a client given a username, a
        remote server's URL, and a user secret.

        If no remote URL is provided, "http://localhost:5000" is assumed.

        If no user secret is provided, this constructor generates a
        new one.
        """
        self._remote_url = remote_url if remote_url else "http://localhost:5000"
        self._client_id = str(uuid.uuid4())

        self._username = username
        self._server_session_token = None

        self._user_secret = crypto.UserSecret(user_secret)

        self._auth_secret = self._user_secret.get_auth_secret()
        self._symmetric_auth = crypto.MessageAuthenticationCode(
            self._user_secret.get_symmetric_key()
        )

        self._device_public_key_signer = (
            crypto.PublicKeySignature()
        )  # not derived from user secret---every device gets its own key pair

        self._photos: t.List[bytes] = []  # list of photos in put_photo order
        self._last_log_number: int = 0
        self._next_photo_id = 0

        # LAB 2
        self._friends: t.Dict[str, FriendInfo] = {}  # maps usernames to friend state

        # LAB 3
        self._public_key_signer = crypto.PublicKeySignature(
            self._user_secret.get_signing_secret_key()
        )
        self._authenticated_encryption = crypto.PublicKeyEncryptionAndAuthentication(
            self._user_secret.get_encrypt_and_auth_secret_key()
        )
        self._albums: t.Dict[str, Album] = {}  # maps album name to album contents
        self._public_profile = types.PublicProfile(
            username=username,
            contents=types.ProfileContents(
                encrypt_public_key=self.encryption_public_key
            ),
            metadata=b"",
        )

    def send_rpc(self, request: types.RpcObject) -> types.RpcObject:
        """
        Sends the given RPC object to the server,
        and returns the server's response.

        To do so, does the following:
        - Converts the given RPC object to JSON
        - Sends a POST request to the server's `/rpc` endpoint
            with the RPC JSON as the body
        - Converts the response JSON into the correct RPC object.

        ## DO NOT CHANGE THIS METHOD

        It is overridden for testing, so any changes will be
        overwritten.
        """
        print("RPC DICT", request.as_rpc_dict())
        r = requests.post(f"{self._remote_url}/rpc", json=request.as_rpc_dict())
        resp = r.json()
        resp_type = self.RESPONSE_MAPPINGS.get(resp["rpc"], None)
        if resp_type is None:
            raise ValueError(f'Invalid response type "{resp["rpc"]}".')
        resp = resp_type.from_dict(resp["data"])
        return resp

    @property
    def username(self) -> str:
        """Get the client's username.

        >>> alice = Client("alice")
        >>> alice.username == "alice"
        True
        """
        return self._username

    @property
    def user_secret(self) -> bytes:
        """Get the client's user secret.

        >>> user_secret = crypto.UserSecret().get_secret()
        >>> alice = Client("alice", user_secret=user_secret)
        >>> alice.user_secret == user_secret
        True
        """
        return self._user_secret.get_secret()

    @property
    def signing_public_key(self) -> bytes:
        """Get the client's public key."""
        return self._public_key_signer.public_key

    @property
    def encryption_public_key(self) -> bytes:
        """
        Get the client's public key to be used for authenticated encryption
        """
        return bytes(self._authenticated_encryption.public_key)

    def register(self) -> None:
        """Register this client's username with the server,
        initializing the user's state on the server.

        If the client is already registered, raise a
        UserAlreadyExistsError.

        Otherwise, save the session token returned by the server for
        use in future requests.

        >>> server = ReferenceServer()
        >>> alice = Client("alice")
        >>> link_client_server(alice, server)

        >>> alice.login()
        Traceback (most recent call last):
                ...
        common.errors.LoginFailedError: failed to log alice in

        >>> alice.register()
        >>> alice.login()
        """
        log = LogEntry(OperationCode.REGISTER, RegisterLogData().encode())
        req = types.RegisterRequest(
            self._client_id,
            self._username,
            self._auth_secret,
            self._public_profile,
            log.encode(),
        )

        resp = self.send_rpc(req)
        assert isinstance(resp, types.RegisterResponse)
        if resp.error is None:
            self._last_log_number += 1
            self._server_session_token = resp.token

        elif resp.error == types.Errcode.USER_ALREADY_EXISTS:
            raise errors.UserAlreadyExistsError(self._username)
        else:
            raise Exception(resp)

    def login(self) -> None:
        """Try to login with to the server with the username and
        auth_secret.

        On success, save the new session token returned by the server
        for use in future requests.

        Otherwise, if the username and auth_secret combination is
        incorrect, raise a LoginFailedError.

        >>> server = ReferenceServer()
        >>> alice = Client("alice")
        >>> link_client_server(alice, server)
        >>> alice.login()
        Traceback (most recent call last):
                ...
        common.errors.LoginFailedError: failed to log alice in

        >>> alice.register()
        >>> alice.login()

        >>> not_alice = Client("alice", server)
        >>> link_client_server(not_alice, server)
        >>> not_alice.login()
        Traceback (most recent call last):
                ...
        common.errors.LoginFailedError: failed to log alice in

        See also: Client.register
        """
        req = types.LoginRequest(
            client_id=self._client_id,
            username=self._username,
            auth_secret=self._auth_secret,
        )
        resp = self.send_rpc(req)
        assert isinstance(resp, types.LoginResponse)
        if resp.error is None:
            self._server_session_token = resp.token
        elif resp.error == types.Errcode.LOGIN_FAILED:
            raise errors.LoginFailedError(self._username)
        else:
            raise Exception(resp)

    def update_public_profile(self, values: t.Dict[str, t.Any]) -> None:
        """Update user public profile with the given fields."""
        # TODO (lab0): Update te local public profile based on the given values and update the server
        self._public_profile["contents"].update(values)
        req = types.UpdatePublicProfileRequest(
            client_id=self._client_id,
            username=self._username,
            token=self._server_session_token,
            public_profile=self._public_profile,
        )
        resp = self.send_rpc(req)
        assert isinstance(resp, types.UpdatePublicProfileResponse)
        if resp.error == types.Errcode.INVALID_TOKEN:
            raise errors.InvalidTokenError()
        elif resp.error is not None:
            raise Exception(resp)

    def get_friend_public_profile(self, friend_username: str) -> types.PublicProfile:
        """Obtain the public profile of another user.

        The user must be a "friend" (i.e. added by `add_friend()`)
        """
        # TODO (lab0): Fetch and return the public profile of the user friend_username
        if friend_username != self.username and friend_username not in self._friends:
            raise errors.UnknownUserError(friend_username)
        req = types.GetFriendPublicProfileRequest(
            client_id=self._client_id,
            username=self._username,
            token=self._server_session_token,
            friend_username=friend_username,
        )
        resp = self.send_rpc(req)
        assert isinstance(resp, types.GetFriendPublicProfileResponse)
        if resp.error == types.Errcode.INVALID_TOKEN:
            raise errors.InvalidTokenError()
        elif resp.error is not None:
            raise Exception(resp)
        else:
            return resp.public_profile

    def list_photos(self) -> t.List[int]:
        """Fetch a list containing the photo id of each photo stored
        by the user.

        >>> server = ReferenceServer()
        >>> alice = Client("alice", server)
        >>> link_client_server(alice, server)
        >>> alice.register()
        >>> photo_blob = b'PHOTOOO'
        >>> alice.put_photo(photo_blob)
        0
        >>> photo_blob = b'PHOOOTO'
        >>> alice.put_photo(photo_blob)
        1
        >>> photo_blob = b'PHOOT0O'
        >>> alice.put_photo(photo_blob)
        2
        >>> alice.list_photos()
        [0, 1, 2]
        """
        self._synchronize()

        return list(range(self._next_photo_id))

    def get_photo(self, photo_id) -> bytes:
        """Get a photo by ID.

        >>> server = ReferenceServer()
        >>> alice = Client("alice")
        >>> link_client_server(alice, server)
        >>> alice.register()
        >>> photo_blob = b'PHOTOOO'
        >>> photo_id = alice.put_photo(photo_blob)
        >>> photo_id
        0
        >>> alice._fetch_photo(photo_id)
        b'PHOTOOO'
        >>> alice._fetch_photo(1)
        Traceback (most recent call last):
                ...
        common.errors.PhotoDoesNotExistError: photo with ID 1 does not exist
        """
        self._synchronize()

        if photo_id < 0 or photo_id >= len(self._photos):
            raise errors.PhotoDoesNotExistError(photo_id)
        return self._photos[photo_id]

    def _push_log_entry(self, log_entry: LogEntry) -> None:
        """
        Push the given log entry to the server
        """
        encoded_log_entry = log_entry.encode()
        req = types.PushLogEntryRequest(
            client_id=self._client_id,
            username=self._username,
            token=self._server_session_token,
            encoded_log_entry=encoded_log_entry,
        )
        resp = self.send_rpc(req)
        assert isinstance(resp, types.PushLogEntryResponse)
        if resp.error:
            raise errors.RpcError

    def _fetch_photo(self, photo_id, user: t.Optional[str] = None) -> bytes:
        """Get a photo from the server using the unique PhotoID.

        If `user` is specified, fetches the photo for the given
        user. Otherwise, fetches for this user.

        >>> server = ReferenceServer()
        >>> alice = Client("alice", server)
        >>> link_client_server(alice, server)
        >>> alice.register()
        >>> photo_blob = b'PHOTOOO'
        >>> photo_id = alice.put_photo(photo_blob)
        >>> photo_id
        0
        >>> alice._fetch_photo(photo_id)
        b'PHOTOOO'
        >>> alice._fetch_photo(1)
        Traceback (most recent call last):
                ...
        common.errors.PhotoDoesNotExistError: photo with ID 1 does not exist
        """
        req = types.GetPhotoRequest(
            client_id=self._client_id,
            username=self._username,
            token=self._server_session_token,
            photo_id=photo_id,
            photo_owner=user or self._username,  # fetch own photo if unspecified
        )
        resp = self.send_rpc(req)
        assert isinstance(resp, types.GetPhotoResponse)
        if resp.error == types.Errcode.INVALID_TOKEN:
            raise errors.InvalidTokenError()
        elif resp.error == types.Errcode.PHOTO_DOES_NOT_EXIST:
            raise errors.PhotoDoesNotExistError(photo_id)
        elif resp.error is not None:
            raise Exception(resp)
        return resp.photo_blob

    def put_photo(self, photo_blob: bytes):
        """Append a photo_blob to the server's database.

        On success, this returns the unique photo_id associated with
        the newly-added photo.

        >>> server = ReferenceServer()
        >>> alice = Client("alice", server)
        >>> link_client_server(alice, server)
        >>> alice.register()
        >>> photo_blob = b'PHOTOOO'
        >>> alice.put_photo(photo_blob)
        0
        >>> photo_blob = b'PHOOOTO'
        >>> alice.put_photo(photo_blob)
        1
        >>> photo_blob = b'PHOOT0O'
        >>> alice.put_photo(photo_blob)
        2
        """
        self._synchronize()

        photo_id = self._next_photo_id

        log = LogEntry(OperationCode.PUT_PHOTO, PutPhotoLogData(photo_id).encode())
        req = types.PutPhotoRequest(
            client_id=self._client_id,
            username=self._username,
            token=self._server_session_token,
            encoded_log_entry=log.encode(),
            photo_blob=photo_blob,
            photo_id=photo_id,
        )

        resp = self.send_rpc(req)
        assert isinstance(resp, types.PutPhotoResponse)
        if resp.error == types.Errcode.INVALID_TOKEN:
            raise errors.InvalidTokenError()
        elif resp.error is not None:
            raise Exception(resp)

        self._record_new_photo(photo_blob)
        self._last_log_number += 1
        return photo_id

    def _record_new_photo(self, photo_blob):
        """
        Locally record a new photo.
        """
        self._next_photo_id += 1
        self._photos.append(photo_blob)

    def _synchronize(self):
        """Synchronize the client's state against the server.

        On failure, this raises a SynchronizationError.

        >>> server = ReferenceServer()
        >>> alice = Client("alice", server)
        >>> link_client_server(alice, server)
        >>> alice.register()
        >>> user_secret = alice.user_secret
        >>> alicebis = Client("alice", server, user_secret)
        >>> link_client_server(alicebis, server)
        >>> alicebis.login()
        >>> alicebis._synchronize()
        >>> alice.login()
        >>> photo_blob = b'PHOTOOO'
        >>> alice._synchronize()
        >>> alice.put_photo(photo_blob)
        0
        >>> photo_blob = b'PHOOOTO'
        >>> alice.put_photo(photo_blob)
        1
        >>> alicebis.login()
        >>> photo_blob = b'PHOOT0O'
        >>> alicebis._synchronize()
        >>> photo_blob = b'PHOOT0O'
        >>> alicebis.put_photo(photo_blob)
        2
        """
        req = types.SynchronizeRequest(
            client_id=self._client_id,
            username=self._username,
            token=self._server_session_token,
            min_version_number=self._last_log_number,
        )
        resp = self.send_rpc(req)
        assert isinstance(resp, types.SynchronizeResponse)

        if resp.error == types.Errcode.INVALID_TOKEN:
            raise errors.InvalidTokenError()
        elif resp.error == types.Errcode.VERSION_TOO_HIGH:
            raise errors.SynchronizationError(errors.VersionTooHighError())
        elif resp.error is not None:
            raise Exception(resp)

        for encoded in resp.encoded_log_entries:
            try:
                log = LogEntry.decode(encoded)
            except errors.MalformedEncodingError as e:
                raise errors.SynchronizationError(e)
            if log.opcode == OperationCode.PUT_PHOTO.value:
                log_data = PutPhotoLogData.decode(log.data)
                photo_blob = self._fetch_photo(log_data.photo_id)
                self._record_new_photo(photo_blob)
            self._last_log_number += 1

    def invite_device(self, device_public_key: bytes) -> None:
        # TODO (lab2) - before then, these can be blank
        pass

    def accept_invite(self, inviter_public_key: bytes) -> None:
        # TODO (lab2)
        pass

    def revoke_device(self, device_public_key: bytes) -> None:
        # TODO (lab2)
        pass

    def add_friend(
        self, friend_username: str, friend_signing_public_key: bytes
    ) -> None:
        """
        Adds the person with the given username to the local
        friends list, marking the given public key as trusted.

        If the friend already exists, overwrites their public key
        with the provided one.
        """
        self._friends[friend_username] = FriendInfo(
            set([friend_signing_public_key]), [], 0
        )

    def get_friend_photos(self, friend_username) -> t.List[bytes]:
        self._synchronize_friend(friend_username)
        return self._friends[friend_username].photos

    def _synchronize_friend(self, friend_username: str):
        """
        Update the state of the given friend locally
        based on the friend's log in the server.
        """
        if friend_username not in self._friends:
            raise errors.UnknownUserError(friend_username)
        friend_info = self._friends[friend_username]
        req = types.SynchronizeFriendRequest(
            self._client_id, friend_username, friend_info.last_log_number
        )
        resp = self.send_rpc(req)
        assert isinstance(resp, types.SynchronizeFriendResponse)

        if resp.error == types.Errcode.VERSION_TOO_HIGH:
            raise errors.SynchronizationError(errors.VersionTooHighError())
        elif resp.error is not None:
            raise Exception(resp)

        for encoded in resp.encoded_friend_log_entries:
            try:
                log = LogEntry.decode(encoded)
            except errors.MalformedEncodingError as e:
                raise errors.SynchronizationError(e)
            if log.opcode == OperationCode.PUT_PHOTO.value:
                log_data = PutPhotoLogData.decode(log.data)
                photo_blob = self._fetch_photo(log_data.photo_id, friend_username)
                friend_info.photos.append(photo_blob)
            friend_info.last_log_number += 1

    def create_shared_album(
        self, album_name: str, photos: t.List[bytes], friends: t.List[str]
    ):
        """Create a new private album with name name_album photos in photos
        The album will be uploaded to the server.
        The photos should only be accessible to the users listed in friends.

        All friends in `friends` must have been added to this device via `add_friend()` beforehand.
        """
        friends_pp_mapping = {
            username: self.get_friend_public_profile(username) for username in friends
        }
        if self.username not in friends_pp_mapping:
            friends_pp_mapping[self.username] = self._public_profile
        album = Album(
            photos=photos, owner=self.username, friends=friends_pp_mapping, metadata={}
        )
        self._albums[album_name] = album
        self._upload_album(album_name)

    def _upload_album(self, album_name: str):
        album = self._albums[album_name]
        req = types.UploadAlbumRequest(
            self._client_id,
            self._username,
            self._server_session_token,
            album_name,
            album.as_dict(),
        )
        resp = self.send_rpc(req)
        assert isinstance(resp, types.UploadAlbumResponse)

        if resp.error == types.Errcode.INVALID_TOKEN:
            raise errors.InvalidTokenError()
        elif resp.error is not None:
            raise Exception(resp)

    def get_album(self, album_name: str) -> types.PhotoAlbumDict:
        """Get an album from the server using its name and the owner's username.
        If the client is part of the friends given access to the album, it will have access to the photos.

        Note: the owner must have been added as a friend to the device using add_friend.
        """

        req = types.GetAlbumRequest(
            self._client_id, self._username, self._server_session_token, album_name
        )
        resp = self.send_rpc(req)
        assert isinstance(resp, types.GetAlbumResponse)

        if (
            resp.album["owner"] != self.username
            and resp.album["owner"] not in self._friends
        ):
            raise errors.AlbumOwnerError(resp.album["owner"])

        if resp.error == types.Errcode.INVALID_TOKEN:
            raise errors.InvalidTokenError()
        if resp.error == types.Errcode.ALBUM_DOES_NOT_EXIST:
            raise errors.AlbumPermissionError(album_name)
        elif resp.error is not None:
            raise Exception(resp)

        if self._username not in resp.album["friends"]:
            raise errors.AlbumPermissionError(album_name)
        self._albums[album_name] = Album.from_dict(resp.album)
        return resp.album

    def add_friend_to_album(self, album_name: str, friend_username: str):
        """Add a friend to an existing album with name album_name.
        Only the owner of the album can modify the list of friends.

        Note: the friend must have been added as a friend to the device using add_friend.
        If they are not, raise an errors.UnknownUserError.
        """
        if friend_username not in self._friends:
            raise errors.UnknownUserError(friend_username)

        if not self._albums[album_name].owner == self.username:
            return errors.AlbumOwnerError(album_name)
        self.get_album(album_name)
        friend_pp = self.get_friend_public_profile(friend_username)
        self._albums[album_name].add_friend(friend_pp)
        self._upload_album(album_name)

    def remove_friend_from_album(self, album_name: str, friend_username: str):
        """Add a friend to an existing album with name album_name.
        Only the owner of the album can modify the list of friends.
        """

        if not self._albums[album_name].owner == self.username:
            return errors.AlbumOwnerError(album_name)
        self.get_album(album_name)
        self._albums[album_name].remove_friend(friend_username)
        self._upload_album(album_name)

    def add_photo_to_album(self, album_name: str, photo: bytes):
        """Add a photo to an existing album with name album_name.
        Only friends of the album can add photos.

        Note: the owner of the album must have been added as a friend on this device.
        """

        self.get_album(album_name)
        self._albums[album_name].add_photo(photo)
        self._upload_album(album_name)


@dataclass
class Album:
    """
    A class to make it easier to generate and modify photo albums
    """

    photos: t.List[bytes]
    owner: str
    friends: t.Dict[str, types.PublicProfile]  # username to public profile
    metadata: t.Dict[str, t.Any]

    def as_dict(self) -> types.PhotoAlbumDict:
        return {
            "photos": self.photos,
            "owner": self.owner,
            "friends": self.friends,
            "metadata": codec.encode(self.metadata),
        }

    @staticmethod
    def from_dict(data: types.PhotoAlbumDict) -> "Album":
        return Album(
            photos=data["photos"],
            owner=data["owner"],
            friends=data["friends"],
            metadata=codec.decode(data["metadata"]),
        )

    def add_photo(self, photo: bytes) -> None:
        """
        adds the given photo blob to the album
        """
        self.photos.append(photo)

    def add_friend(self, friend_pp: types.PublicProfile) -> None:
        """
        Add the given friend to the album
        """
        self.friends[friend_pp["username"]] = friend_pp

    def remove_friend(self, friend_username: str) -> None:
        """
        remove the given friend's permission from the album
        """
        del self.friends[friend_username]

