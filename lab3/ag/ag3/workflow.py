
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
        print(f"\tReceived incorrect album (basic 1) contents! Expected {expected}, got {photos_received}")
        return False

    try:
        photos_received = carlos.get_album("my_album")["photos"]
        return False
    except errors.AlbumPermissionError:
        alice.add_friend(carlos.username, carlos.signing_public_key)
        alice.add_friend_to_album("my_album", carlos.username)
        photos_received = bob.get_album("my_album")["photos"]
        if photos_received != expected:
            print(f"\tReceived incorrect album (basic 2) contents! Expected {expected}, got {photos_received}")
            return False

    photos_received = carlos.get_album("my_album")["photos"]
    if photos_received != expected:
        print(f"\tReceived incorrect album (basic 3) contents! Expected {expected}, got {photos_received}")
        return False
    photos_received = alice.get_album("my_album")["photos"]
    if photos_received != expected:
        print(f"\tReceived incorrect album (basic 4) contents! Expected {expected}, got {photos_received}")
        return False

    new_photo = b'photo_bob'
    bob.add_photo_to_album("my_album", new_photo)
    photos_received = carlos.get_album("my_album")["photos"]
    expected.append(new_photo)
    if photos_received != expected:
        print(f"\tReceived incorrect album (basic 5) contents! Expected {expected}, got {photos_received}")
        return False
    
    photos_received = alice.get_album("my_album")["photos"]
    if not photos_received == expected:
        print(f"\tReceived incorrect album (basic 6) contents! Expected {expected}, got {photos_received}")
        return False

    alice.remove_friend_from_album("my_album", "carlos")
    try:
        photos_received = carlos.get_album("my_album")["photos"]
        print(f"\tReceived incorrect album (basic 7) contents! Expected {expected}, got {photos_received}")
        return False
    except errors.AlbumPermissionError:
        pass
    return True
