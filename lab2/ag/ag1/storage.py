class Lab1Storage:
    def __init__(self):
        self.userbase = {}
        self.log_index_to_photo_id = {}
        self.photo_id_to_log_index = {}

    def check_user_registered(self, username):
        return username in self.userbase

    def check_token(self, username, token):
        return (username in self.userbase) and (self.userbase[username].token == token)

    def add_new_user(self, username, auth_secret, token):
        self.userbase[username] = UserData(username, auth_secret, token)

    def log_operation(self, username, log_entry):
        index = len(self.userbase[username].history)
        self.userbase[username].history.append(log_entry)
        return index

    def check_auth_secret(self, username, auth_secret):
        return self.userbase[username].auth_secret == auth_secret

    def update_user_token(self, username, token):
        self.userbase[username].token = token

    def get_user_token(self, username):
        return self.userbase[username].token

    def store_photo(self, username, photo_id, photo_blob):
        self.userbase[username].photobase[photo_id] = PhotoData(
            username, photo_id, photo_blob
        )

    def swap_photo_blobs(self, username, pid0, pid1):
        photo_blob0 = self.userbase[username].photobase[pid0].photo_blob
        photo_blob1 = self.userbase[username].photobase[pid1].photo_blob
        self.userbase[username].photobase[pid0] = PhotoData(username, pid0, photo_blob1)
        self.userbase[username].photobase[pid1] = PhotoData(username, pid1, photo_blob0)

    def load_photo(self, username, photo_id):
        if photo_id in self.userbase[username].photobase:
            return self.userbase[username].photobase[photo_id]
        else:
            return None

    def list_user_photos(self, username):
        return list(self.userbase[username].photobase.keys())

    def latest_user_version(self, username):
        # return self.userbase[username].history[-1].tag.version_number
        return len(self.userbase[username].history) - 1

    def user_history(self, username, min_version_number):
        return self.userbase[username].history[min_version_number:]

    def _map_log(self, username, log_index, photo_id):
        self.log_index_to_photo_id[(username, log_index)] = photo_id
        self.photo_id_to_log_index[(username, photo_id)] = log_index


class UserData:
    def __init__(self, username, auth_secret, token, photobase=None, history=None):
        self.username = username
        self.auth_secret = auth_secret
        self.token = token

        if photobase is None:
            photobase = {}
        if history is None:
            history = []
        self.photobase = photobase
        self.history = history

    # defined to help with debugging
    def __repr__(self):
        return self.__str__()


class PhotoData:
    def __init__(self, username, photo_id, photo_blob):
        self.username = username
        self.photo_id = photo_id
        self.photo_blob = photo_blob

    # defined to help with debugging
    def __repr__(self):
        return self.__str__()


if __name__ == "__main__":
    import doctest

    doctest.testmod()

