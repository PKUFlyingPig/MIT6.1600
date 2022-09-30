# 6.1600 Lab 2

In this lab, you will extend the photo-storage platform that we secured in lab 1 to support viewing and authenticating friends' photos. In doing so, you will make use of public-key signatures to support multiple devices. 

# Code Overview

The code is largely the same as in lab 1. However, we have added support for public-key cryptography to the client. Each client has a randomly generated public key (`Client.public_key`) and a `PublicKeySignature` object that can be used to generate signatures. Clients can use `verify_sign()` to check these signatures. We have also added several functions to support adding __and revoking__ multiple devices using per-device keys:

- `invite_device(device_public_key)` allows inviting a new device to join a user's account. 
- `accept_invite(inviter_public_key)` is called by an invited device with the public key of the device that invited them.
- `revoke_device(device_public_key)` is called when one device on a user's account would like to revoke the access of some other device (specified by public key) on the user's account.

We have also added methods to support adding "friends" and viewing their photos:

- `add_friend(friend_username, friend_public_key)` is called when one user would like to add another user as a friend. We have given a starter implementation of this function for you. For simplicity, we do not require you to synchronize the friend list between the different devices belonging to the same user---that is, if Alice wants to view Bob's photos on her two devices, she must call `add_friend()` to add Bob on each of her devices separately.
- `get_friend_photos(friend_username)` returns the current list of photos in the given friend's album. We have provided a starter implementation of a helper function `_synchronize_friend` to help you get started---feel free to use it or delete it. 

Note that all of these involve manually entering a device public key. In a real system, this might be done through, for example, QR codes. Systems like Keybase and Signal use a strategy like this.

We have also added a generic `Client.push_log_entry` method that allows you to push a log entry of arbitrary bytes to the server. This allows you to add new log entries if you wish. The `LogEntry` class has also been moved into its own file, `client/log_entry.py`, which you are allowed to edit as much as you like.

# Specification

In addition to the requirements outlined below that outline behavior between multiple users, we want to maintain the correctness and security properties we achieved in lab 1. We have included the tests from lab 1 in this lab, with point values scaled down by a factor of 10.

## Correctness
Given an honest server (e.g., `ReferenceServer`), correct behavior is defined by the following, in addition to the correctness requirements of lab 1:

- If a user calls `add_friend(friend, friend_public_key)` followed by `get_friend_photos(friend)`, all photos uploaded by any of the friend's devices that were authorized at the time of upload should be returned.
    - A device is "authorized" by default if it is the first device to register a given username. 
    - After one device has registered under a username, other devices are "authorized" for that username if:
        - An authorized device has called `Client.invite_device(device_public_key)` and
        - The invited device has called `Client.accept_invite(inviter_public_key)` and 
        - No authorized device has called `Client.revoke_friend(device_public_key)`

Authorization is always relative to the point at which an action occured. For example, consider the following sequence of events:

1. user "B" registers with their device `b_1`
2. `b_1` adds a new device `b_2`
3. `b_2` uploads a photo `b_2_photo`
4. `b_1` revokes `b_2`
5. user "A" adds "B" as a friend using `b_1`'s public key, then lists "B"'s photos. `b_2_photo` should be included, even though `b_2` is now unauthorized.

Our general correctness requirement, given an honest server and honest clients, is: if a user A that adds another user B as a friend and then calls `get_friend_photos(B)`, the photos returned should be consistent with the result of `list_photos()` on any of B's devices.

Note that when adding a friend, _any_ public key that is currently authorized to that user may be specified. However, even photos that were added before that public key became valid must be verified and returned.

## Security
### Threat Model

Our threat model has expanded a bit from lab 1. While in lab 1, we considered only a malicious _server_ and assumed that all clients are honest, in this lab we separately consider the possibility that one of a given user's devices may become compromised. 

### Security Goals

With that in mind, there are three scenarios we want to consider. In each, we are aiming for the best security possible given our system structure. The specific scenarios are:

1. _Device compromise with an honest server_. If one or more of a user's devices becomes compromised, but the server is honest, we would like to guarantee that a friend who tries to view that user's photos sees only photos from devices that were associated with the user's account at the time they posted the photo---that is, they were legitimately added and they were not revoked (yet).

2. _Server compromise with honest devices_. This is the same scenario as in Lab 1, and in this case we would like similar guarantees as in Lab 1 for client-to-client synchronization between clients of the same user: the server should not be able to modify the list of photos. For this lab, we are also concerned with the list of photos as it appears to _a friend's client_. We would like for this list to be some prefix of the "real" list with a compromised server.

3. _Server and device compromise_. In this case, it becomes more difficult to provide guarantees about revoking that client. However, we would still like to guarantee something: if an authorized device B_1 revokes another authorized device B_2 that belongs to the same user, a friend A must __either__ see no more changes from device B_1 or see no more changes from device B_2.

Note that a friend should _not_ try to reconcile an invalid log into something valid by ignoring entries or applying other modifications to the log. If a friend discovers that a user's state has been tampered with, the friend should raise an `errors.SynchronizationError`. 

### Non-goals

Note that we still are not worrying about secrecy---in this system, any user can see all other users' photos.

# Your Job
Your job is to modify the files in `client/` to support the above correctness and security properties.

To submit, please upload to Gradescope a `.zip` file containing the `client` folder and the files inside.

