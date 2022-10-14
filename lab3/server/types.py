import typing as t
from common import types


class UserData:
    def __init__(self, username: str, auth_secret, token: bytes, public_profile: types.PublicProfile):
        self.username = username
        self.public_profile = public_profile
        self.auth_secret = auth_secret
        self.token = token
        self.photobase: t.Dict[int, PhotoData] = {}
        self.history: t.List[bytes] = []  # list of log entries for the user


class PhotoData:
    def __init__(self, username, photo_id, photo_blob):
        self.username = username
        self.photo_id = photo_id
        self.photo_blob = photo_blob

