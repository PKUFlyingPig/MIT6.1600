import typing as t
import secrets
import common.codec as codec

from collections import defaultdict

import common.types as types
from server.spec import Server
from server.types import PhotoData, UserData


class ReferenceServer(Server):
    """A server implementation that meets the spec.  Useful for testing.
    Servers used in test cases will not always follow the spec.
    """

    def __init__(self):
        self._storage = InMemoryStorage()

    def register_user(self, request: types.RegisterRequest) -> types.RegisterResponse:
        if not self._storage.check_user_registered(request.username):
            token = secrets.token_hex(64)
            self._storage.add_new_user(
                request.username, request.auth_secret, token, request.public_profile
            )
            self._storage.log_operation(request.username, request.encoded_log_entry)
            return types.RegisterResponse(None, token)
        else:
            return types.RegisterResponse(types.Errcode.USER_ALREADY_EXISTS, None)

    def login(self, request: types.LoginRequest) -> types.LoginResponse:
        if self._storage.check_user_registered(
            request.username
        ) and self._storage.check_auth_secret(request.username, request.auth_secret):
            token = secrets.token_hex(64)
            self._storage.update_user_token(request.username, token)
            return types.LoginResponse(None, token)
        else:
            return types.LoginResponse(types.Errcode.LOGIN_FAILED, None)

    def update_public_profile(
        self, request: types.UpdatePublicProfileRequest
    ) -> types.UpdatePublicProfileResponse:
        if not self._storage.check_token(request.username, request.token):
            return types.UpdatePublicProfileResponse(types.Errcode.INVALID_TOKEN)
        self._storage.update_public_profile(request.username, request.public_profile)
        return types.UpdatePublicProfileResponse(None)

    def get_friend_public_profile(
        self, request: types.GetFriendPublicProfileRequest
    ) -> types.GetFriendPublicProfileResponse:
        if not self._storage.check_token(request.username, request.token):
            return types.GetFriendPublicProfileResponse(
                types.Errcode.INVALID_TOKEN, None
            )
        public_profile = self._storage.get_friend_public_profile(
            request.friend_username
        )
        return types.GetFriendPublicProfileResponse(None, public_profile)

    def put_photo_user(self, request: types.PutPhotoRequest) -> types.PutPhotoResponse:
        if not self._storage.check_token(request.username, request.token):
            return types.PutPhotoResponse(types.Errcode.INVALID_TOKEN, None)

        self._storage.store_photo(
            request.username, request.photo_id, request.photo_blob
        )
        self._storage.log_operation(request.username, request.encoded_log_entry)
        return types.PutPhotoResponse(None)

    def get_photo_user(self, request: types.GetPhotoRequest) -> types.GetPhotoResponse:
        """
        Gets the photo contents for the given photo_id and the given owner
        """
        if not self._storage.check_token(request.username, request.token):
            return types.GetPhotoResponse(types.Errcode.INVALID_TOKEN, None)

        photo = self._storage.load_photo(request.photo_owner, request.photo_id)
        if photo != None:
            return types.GetPhotoResponse(None, photo.photo_blob)
        else:
            return types.GetPhotoResponse(types.Errcode.PHOTO_DOES_NOT_EXIST, None)

    def push_log_entry(
        self, request: types.PushLogEntryRequest
    ) -> types.PushLogEntryResponse:
        if not self._storage.check_token(request.username, request.token):
            return types.PushLogEntryResponse(types.Errcode.INVALID_TOKEN)

        self._storage.log_operation(request.username, request.encoded_log_entry)

        return types.PushLogEntryResponse(None)

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
        return types.SynchronizeResponse(None, log)

    def synchronize_friend(
        self, request: types.SynchronizeFriendRequest
    ) -> types.SynchronizeFriendResponse:
        server_version = self._storage.latest_user_version(request.friend_username)
        if request.min_version_number > server_version + 1:
            return types.SynchronizeFriendRequest(types.Errcode.VERSION_TOO_HIGH, None)
        log = self._storage.user_history(
            request.friend_username, request.min_version_number
        )
        return types.SynchronizeFriendResponse(None, log)

    def upload_album(
        self, request: types.UploadAlbumRequest
    ) -> types.UploadAlbumResponse:
        if not self._storage.check_token(request.username, request.token):
            return types.UploadAlbumResponse(types.Errcode.INVALID_TOKEN)
        self._storage.update_private_album(request.name, request.album)
        return types.UploadAlbumResponse(None)

    def get_album(self, request: types.GetAlbumRequest) -> types.GetAlbumResponse:
        if not self._storage.check_token(request.username, request.token):
            return types.GetAlbumResponse(types.Errcode.INVALID_TOKEN, None)
        album = self._storage.get_private_album(request.album_name)
        if album == None:
            return types.GetAlbumResponse(types.Errcode.ALBUM_DOES_NOT_EXIST, None)
        return types.GetAlbumResponse(None, album)


class InMemoryStorage:
    def __init__(self):
        self.userbase: t.Dict[str, UserData] = {}
        self._private_albums: t.Dict[str, types.PhotoAlbumDict] = {}

    def check_user_registered(self, username: str) -> bool:
        return username in self.userbase

    def check_token(self, username: str, token: str) -> bool:
        return (username in self.userbase) and (self.userbase[username].token == token)

    def add_new_user(
        self,
        username: str,
        auth_secret: bytes,
        token: str,
        profile: types.PublicProfile,
    ) -> None:
        self.userbase[username] = UserData(username, auth_secret, token, profile)

    def update_public_profile(
        self, username: str, new_public_profile: types.PublicProfile
    ) -> None:
        self.userbase[username].public_profile = new_public_profile

    def get_friend_public_profile(self, friend_username: str) -> types.PublicProfile:
        return self.userbase[friend_username].public_profile

    def log_operation(self, username: str, log_entry: bytes) -> None:
        self.userbase[username].history.append(log_entry)

    def check_auth_secret(self, username: str, auth_secret: bytes) -> bool:
        return self.userbase[username].auth_secret == auth_secret

    def update_user_token(self, username: str, token: str) -> None:
        self.userbase[username].token = token

    def store_photo(self, username: str, photo_id: int, photo_blob: bytes) -> None:
        self.userbase[username].photobase[photo_id] = PhotoData(
            username, photo_id, photo_blob
        )

    def load_photo(self, username: str, photo_id: int) -> PhotoData:
        if photo_id in self.userbase[username].photobase:
            return self.userbase[username].photobase[photo_id]
        else:
            return None

    def list_user_photos(self, username: str) -> t.List[int]:
        return list(self.userbase[username].photobase.keys())

    def latest_user_version(self, username: str) -> int:
        return len(self.userbase[username].history) - 1

    def user_history(self, username: str, min_version_number: int) -> t.List[bytes]:
        return self.userbase[username].history[min_version_number:]

    def update_private_album(self, album_name: str, album: types.PhotoAlbumDict):
        self._private_albums[album_name] = album

    def get_private_album(self, album_name: str) -> types.PhotoAlbumDict:
        if album_name not in self._private_albums:
            return None
        return self._private_albums[album_name]

