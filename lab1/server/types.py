import typing as t
from common import types


class UserData:
    def __init__(self, username, auth_secret, token):
        self.username = username
        self.public_profile = types.PublicProfile(username, {})
        self.auth_secret = auth_secret
        self.token = token
        self.photobase: t.Dict[int, PhotoData] = {}
        self.history: t.List[bytes] = []  # list of log entries for the user


class PhotoData:
    def __init__(self, username, photo_id, photo_blob):
        self.username = username
        self.photo_id = photo_id
        self.photo_blob = photo_blob

