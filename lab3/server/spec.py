# this just holds the type definitions for the server,
# to be implemented by actual servers (non-malicious or otherwise)

from abc import ABC, abstractmethod

import common.types as types

# if we are gonna use pytest, I don't think we really need this. We can just
# have a main "server" implementation that we mock out.
class Server(ABC):
    """The spec for a server."""

    @abstractmethod
    def register_user(self, request: types.RegisterRequest) -> types.RegisterResponse:
        pass

    @abstractmethod
    def login(self, request: types.LoginRequest) -> types.LoginResponse:
        pass

    @abstractmethod
    def update_public_profile(
        self, request: types.UpdatePublicProfileRequest
    ) -> types.UpdatePublicProfileResponse:
        pass

    @abstractmethod
    def get_friend_public_profile(
        self, request: types.GetFriendPublicProfileRequest
    ) -> types.GetFriendPublicProfileResponse:
        pass

    @abstractmethod
    def put_photo_user(self, request: types.PutPhotoRequest) -> types.PutPhotoResponse:
        pass

    @abstractmethod
    def get_photo_user(self, request: types.GetPhotoRequest) -> types.GetPhotoResponse:
        pass

    @abstractmethod
    def push_log_entry(
        self, request: types.PushLogEntryRequest
    ) -> types.PushLogEntryResponse:
        pass

    @abstractmethod
    def synchronize(
        self, request: types.SynchronizeRequest
    ) -> types.SynchronizeResponse:
        pass

    @abstractmethod
    def synchronize_friend(
        self, request: types.SynchronizeFriendRequest
    ) -> types.SynchronizeFriendResponse:
        pass

    @abstractmethod
    def upload_album(self, request: types.UploadAlbumRequest) -> types.UploadAlbumResponse:
        pass

    @abstractmethod
    def get_album(self, request: types.GetAlbumRequest) -> types.GetAlbumResponse:
        pass
