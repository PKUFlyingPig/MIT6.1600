from client import client
import common.types as types
import common.errors as errors


class ImpoliteClient(client.Client):
    """
    This client will try to do things dishonestly
    """

    def get_album(self, album_name: str) -> types.PhotoAlbumDict:
        """Get an album from the server using its name and the owner's username.
        If the client is part of the friends given access to the album, it will have access to the photos.

        Note: the owner must have been added as a friend to the device using add_friend
        """

        req = types.GetAlbumRequest(
            self._client_id, self._username, self._server_session_token, album_name
        )
        resp = self.send_rpc(req)
        assert isinstance(resp, types.GetAlbumResponse)

        if resp.error == types.Errcode.INVALID_TOKEN:
            raise errors.InvalidTokenError()
        if resp.error == types.Errcode.ALBUM_DOES_NOT_EXIST:
            raise errors.AlbumPermissionError(album_name)
        elif resp.error is not None:
            raise Exception(resp)

        return resp.album

    def add_friend_to_album(self, album_name: str, friend_username: str):
        """Add a friend to an existing album with name album_name.
        Only the owner of the album can modify the list of friends.

        Note: the friend must have been added as a friend to the device using add_friend
        """
        # skip these checks
        # if friend_username not in self._friends:
        #     raise errors.UnknownUserError(friend_username)

        # if not self._albums[album_name].owner == self.username:
        #     return errors.AlbumOwnerError(album_name)
        album = self.get_album(album_name)
        friend_pp = self.get_friend_public_profile(friend_username)

        album["friends"][friend_username] = friend_pp
        self._upload_album(album_name, album)

    def _upload_album(self, album_name: str, album: types.PhotoAlbumDict):
        """
        Upload the given album under the given name
        """
        req = types.UploadAlbumRequest(
            self._client_id,
            self._username,
            self._server_session_token,
            album_name,
            album,
        )
        resp = self.send_rpc(req)
        assert isinstance(resp, types.UploadAlbumResponse)

        if resp.error == types.Errcode.INVALID_TOKEN:
            raise errors.InvalidTokenError()
        elif resp.error is not None:
            raise Exception(resp)

