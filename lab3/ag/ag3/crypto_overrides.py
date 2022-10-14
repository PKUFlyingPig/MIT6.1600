#!/usr/bin/env python3

import json
import secrets
import hmac
import hashlib
import typing as t
from nacl.signing import SigningKey, VerifyKey
from nacl.public import PrivateKey, PublicKey, Box
from nacl.secret import SecretBox
from nacl.utils import random
from collections import defaultdict
import nacl
from client.client import Client

from common import codec
from common import errors
import common.crypto

DEBUG = False

"""Special Cryptographic Library for Auto Grading"""

hash_function = hashlib.sha3_256

""" Global Data"""
global current_owner  # the user that is currently signing/encrypting things
current_owner: str = "None"
global public_key_to_owner  # maps signing public key to the user that owns that
public_key_to_owner: t.Dict[bytes, str] = {}
global secret_key_to_owner  # maps encryption shared keys and signing private keys to the user that owns it
secret_key_to_owner: t.Dict[bytes, str] = {}
global owner_to_secret_keys  # maps owner to shared encryption keys that they have access to
owner_to_secret_keys: t.Dict[bytes, t.Set[bytes]] = defaultdict(set)
global key_mapping  # maps secret key to corresponding public key and vice versa
key_mapping: t.Dict[bytes, bytes] = {}

ENCRYPTION_TYPES = [
    "Lab3Encryption",
    "Lab3Signature",
    "Lab3EncryptionAndAuthentication",
]


def reset() -> None:
    global current_owner, public_key_to_owner, secret_key_to_owner, owner_to_secret_keys, key_mapping
    current_owner = "None"
    public_key_to_owner = {}
    secret_key_to_owner = {}
    owner_to_secret_keys = defaultdict(set)
    key_mapping = {}


class View:
    """
    Represents the information that a given user
    can have available to her, given the objects and keys
    specified by calls to `add_obj` and `add_keys`.

    Keeps track of available keys and available data,
    where data is non-key material that the user knows about.
    This available data can be used, for example, to verify
    whether a given user knows about the existence of a certain
    photo's contents.
    """

    def __init__(self, user: "Client"):
        """ """
        self.user = user
        self.available_keys: t.Set[bytes] = set(owner_to_secret_keys[user.username])
        self.available_keys |= set(public_key_to_owner.keys())
        self.available_data = set()
        self.encryption_stack = []

    def add_obj(self, obj):
        if DEBUG:
            print(f"adding obj ({self.user.username})", obj)
        self._walk_obj(obj)
        self._decrypt()

    def add_keys(self, keys):
        self.available_keys |= keys

    def _walk_obj(self, obj):
        """
        Go through the given object to find all available information in it.

        If the item is a key, then mark that key as being available
        """
        if DEBUG:
            print("walking obj", repr(obj))
        if obj is None:
            return
        elif type(obj) is list:
            for o in obj:
                self._walk_obj(o)
        elif type(obj) is int:
            self.available_data.add(obj)
        elif type(obj) is dict:
            for k, v in obj.items():
                self._walk_obj(k)
                self._walk_obj(v)
        elif type(obj) is str:
            self.available_data.add(obj)
        elif type(obj) is bytes:
            self._open_bytes(obj)
        else:
            raise TypeError("type of obj ({}) is not encodable".format(type(obj)))

    def _open_bytes(self, b):
        assert type(b) == bytes
        if DEBUG:
            print("working on bytes", b)
        if b in secret_key_to_owner or b in public_key_to_owner:
            if DEBUG:
                print("\t that's a key!")
            # is a key
            self.available_keys.add(b)

        try:
            obj = codec.decode(b)
            if DEBUG:
                print(f"\tdecoded into {obj}")
            if (
                isinstance(obj, dict)
                and "type" in obj
                and obj["type"] in ENCRYPTION_TYPES
            ):
                # this is an "encryption" object
                if DEBUG:
                    print(f"\t-> adding to enc stack")
                self.encryption_stack.append(obj)
            else:
                # not an encryption, just look at the object contents
                self._walk_obj(obj)
        except errors.MalformedEncodingError:
            # not an encoding so just add the bytes
            self.available_data.add(b)

    def _decrypt(self):
        """
        Decrypt all items that have not been decrypted,
        adding newly discovered keys to the available keys
        and newly discovered information to the available info.

        If things cannot be decrypted, they are added back into
        the encryption stack and the process is continued until
        the encryption stack remains the same size after a
        full iteration.
        """
        if DEBUG:
            print(
                "STARTING DECRYPTION. Available keys\n\t",
                "\n\t".join(str(x) for x in self.available_keys),
            )
        while True:
            new_stack = []
            for e in self.encryption_stack:
                if DEBUG:
                    print(f"got {e} from stack, decrypting it.")
                obj = e["data"]
                if e["type"] == "Lab3Encryption":
                    if e["sk"] in self.available_keys:
                        self._walk_obj(obj)
                    else:
                        if DEBUG:
                            print("\t -> can't decrypt")
                        new_stack.append(e)
                elif e["type"] == "Lab3EncryptionAndAuthentication":
                    if e["sk_enc"] in self.available_keys:
                        self._walk_obj(obj)
                    else:
                        if DEBUG:
                            print("\t -> can't decrypt")
                        new_stack.append(e)
                elif e["type"] == "Lab3Signature":
                    self._walk_obj(obj)
                else:
                    raise TypeError("type of encoding is not supported")
            if len(new_stack) == len(self.encryption_stack):
                # we couldn't decrypt anything this round (at fixed point)
                break
            self.encryption_stack = new_stack


class UserSecret(common.crypto.UserSecret):
    """A user secret used for key generation."""

    def __init__(self, secret=None):
        """Wrap secret bytes to generate different user keys.
        If none is provided, generate new secret bytes.
        >>> secret = UserSecret()
        """
        if secret == None:
            self._secret = secrets.token_bytes(32)
        else:
            self._secret = secret
        self._auth_secret = self._generate_auth_secret()
        self._symmetric_key = self._generate_symmetric_key()
        (self._s_sk, self._s_pk) = self._generate_signing_key_pair()
        (self._e_sk, self._e_pk) = self._generate_encrypt_and_auth_key_pair()

    def _generate_auth_secret(self):
        h_ctxt = hash_function()
        h_ctxt.update("auth_secret".encode("utf-8"))
        h_ctxt.update(self._secret)
        sk = h_ctxt.digest()
        secret_key_to_owner[bytes(sk)] = current_owner
        owner_to_secret_keys[current_owner].add(bytes(sk))
        return sk

    def _generate_symmetric_key(self):
        h_ctxt = hash_function()
        h_ctxt.update("symmetric_key".encode("utf-8"))
        h_ctxt.update(self._secret)
        sk = h_ctxt.digest()
        secret_key_to_owner[bytes(sk)] = current_owner
        owner_to_secret_keys[current_owner].add(bytes(sk))
        return sk

    def _generate_signing_key_pair(self):
        h_ctxt = hash_function()
        h_ctxt.update("signing_key_pair".encode("utf-8"))
        h_ctxt.update(self._secret)
        seed_sk = h_ctxt.digest()
        sk = SigningKey(seed_sk)
        pk = sk.verify_key
        public_key_to_owner[bytes(pk)] = current_owner
        secret_key_to_owner[bytes(sk)] = current_owner
        owner_to_secret_keys[current_owner].add(bytes(sk))
        key_mapping[bytes(sk)] = bytes(pk)
        key_mapping[bytes(pk)] = bytes(sk)
        return (sk, pk)

    def _generate_encrypt_and_auth_key_pair(self):
        h_ctxt = hash_function()
        h_ctxt.update("encrypt_and_auth_key_pair".encode("utf-8"))
        h_ctxt.update(self._secret)
        seed_sk = h_ctxt.digest()
        sk = PrivateKey(seed_sk)
        pk = sk.public_key
        public_key_to_owner[bytes(pk)] = current_owner
        secret_key_to_owner[bytes(sk)] = current_owner
        owner_to_secret_keys[current_owner].add(bytes(sk))
        key_mapping[bytes(sk)] = bytes(pk)
        key_mapping[bytes(pk)] = bytes(sk)
        return (sk, pk)


def Lab3Sign(data, sk):
    owner = secret_key_to_owner[sk]
    pk = key_mapping[sk]
    signature = {
        "type": "Lab3Signature",
        "data": data,
        "sk": sk,
        "pk": pk,
        "owner": owner,
    }
    return codec.encode(signature)


def Lab3Ver(data, pk, sig):
    signature = codec.decode(sig)
    if type(signature) is not dict:
        return False
    if signature["type"] != "Lab3Signature":
        return False
    if signature["pk"] == pk and signature["data"] == data:
        return True
    return False


class PublicKeySignature:
    def __init__(self, secret_key: SigningKey = None):
        """Save the key pair.
        If none is provided, generate a new key pair.

        >>> prover = PublicKeySignature()
        """
        if secret_key == None:
            sk = SigningKey.generate()
            self._sk = sk
            secret_key_to_owner[bytes(sk)] = current_owner
            owner_to_secret_keys[current_owner].add(bytes(sk))
            pk = sk.verify_key
            self._pk = pk
            public_key_to_owner[bytes(pk)] = secret_key_to_owner[bytes(sk)]
            key_mapping[bytes(sk)] = bytes(pk)
            key_mapping[bytes(pk)] = bytes(sk)
        else:
            self._sk = secret_key
            self._pk = secret_key.verify_key

    @property
    def public_key(self) -> bytes:
        return self._pk.encode()

    def sign(self, data: bytes) -> bytes:
        """Create a digital signature over the data given the
        signing key.

        >>> fake_secret_key = bytes.fromhex('55fd88856b82d2b3149e8a872e7aeda485e5a2eca1ad3daca52f716472201dee')
        >>> sk = SigningKey(fake_secret_key)
        >>> prover = PublicKeySignature(sk)
        >>> payload = codec.encode([b"Hello ", "Security!", 1])
        >>> prover.sign(payload).hex()
        'fb6c1b9fa40bef32375a8fadb6e9471cd33518cda1a8861238e639b033976dc45aa166e9f430e9020eee1b0c928e24de9a87281cc819f2c9899d143149cb670d'
        """
        if type(data) is not bytes:
            raise TypeError("data must be bytes")
        if bytes(self._sk) not in secret_key_to_owner:
            print("Error this key was not tainted")
        return Lab3Sign(data, bytes(self._sk))


def verify_sign(pk, data, signature):
    """Check the provided message authenticator against the given
    data and secret.

    >>> sk = SigningKey.generate()
    >>> prover = PublicKeySignature(sk)
    >>> payload = codec.encode([b"Hello ", "Security!", 1])
    >>> signature = prover.sign(payload)
    >>> pk = prover.public_key
    >>> verify_sign(pk, payload, signature)
    True
    """
    return Lab3Ver(data, bytes(pk), signature)


def generate_symmetric_secret_key() -> bytes:
    sk = random(SecretBox.KEY_SIZE)
    secret_key_to_owner[bytes(sk)] = current_owner
    owner_to_secret_keys[current_owner].add(bytes(sk))
    return bytes(sk)


def Lab3SymEnc(sk, data: bytes) -> bytes:
    owner = secret_key_to_owner[sk]
    ciphertext = {"type": "Lab3Encryption", "data": data, "sk": sk, "owner": owner}
    return codec.encode(ciphertext)


def Lab3SymDec(sk, ciphertext: bytes) -> bytes:
    enc = codec.decode(ciphertext)
    if type(enc) is not dict:
        raise ValueError("Value not encrypted using common.crypto")
    if enc["type"] != "Lab3Encryption":
        raise ValueError("Value not encrypted symmetrically")
    if enc["sk"] != sk:
        raise ValueError("Invalid Key")
    return enc["data"]


class SymmetricKeyEncryption:
    def __init__(self, secret_key=None):
        """Save the secret encryption key.
        If none is provided, generate a new secret key.

        >>> enc = SymmetricKeyEncryption()
        >>> data = b"hello"
        >>> ciphertxt = enc.encrypt(data)
        >>> plain = enc.decrypt(ciphertxt)
        >>> plain
        b'hello'
        """
        if secret_key == None:
            self._sk = generate_symmetric_secret_key()
            secret_key_to_owner[bytes(self._sk)] = current_owner
            owner_to_secret_keys[current_owner].add(bytes(self._sk))
        else:
            self._sk = secret_key
        self.box = SecretBox(self._sk)

    def encrypt(self, data: bytes) -> bytes:
        if type(data) is not bytes:
            raise TypeError("data must be bytes")
        return Lab3SymEnc(bytes(self._sk), data)

    def decrypt(self, ciphertext):
        return Lab3SymDec(bytes(self._sk), ciphertext)


def Lab3EncAndAuth(pk_enc, sk_auth, data: bytes):
    if pk_enc not in key_mapping or sk_auth not in key_mapping:
        raise KeyError("This private key doesn't match any public key")
    pk_auth = key_mapping[sk_auth]
    sk_enc = key_mapping[pk_enc]
    owner_auth = secret_key_to_owner[sk_auth]
    owner_enc = secret_key_to_owner[sk_enc]
    ciphertext = {
        "type": "Lab3EncryptionAndAuthentication",
        "data": data,
        "sk_auth": sk_auth,
        "pk_auth": pk_auth,
        "sk_enc": sk_enc,
        "pk_enc": pk_enc,
        "owner_auth": owner_auth,
        "owner_enc": owner_enc,
    }
    return codec.encode(ciphertext)


def Lab3DecAndVer(sk_enc, pk_auth, ciphertext):
    enc = codec.decode(ciphertext)
    if type(enc) is not dict:
        raise ValueError("Value not encrypted using common.crypto")
    if enc["type"] != "Lab3EncryptionAndAuthentication":
        raise ValueError(
            "Value not encrypted with common.crypto authenticated encryption"
        )
    if enc["sk_enc"] != sk_enc or enc["pk_auth"] != pk_auth:
        raise ValueError("invalid key")
    return enc["data"]


class PublicKeyEncryptionAndAuthentication:
    def __init__(self, secret_key=None):
        """Save the secret encryption key.
        If none is provided, generate a new secret key.

        >>> sender = PublicKeyEncryptionAndAuthentication()
        >>> receiver = PublicKeyEncryptionAndAuthentication()
        >>> data = b"hello"
        >>> r_pk = receiver.public_key
        >>> s_pk = sender.public_key
        >>> ciphertext = sender.encrypt_and_auth(data, r_pk)
        >>> plain = receiver.decrypt_and_verify(ciphertext, s_pk)
        >>> plain
        b'hello'
        """
        if secret_key == None:
            sk = PrivateKey.generate()
            self._sk = sk
            secret_key_to_owner[bytes(sk)] = current_owner
            owner_to_secret_keys[current_owner].add(bytes(sk))
            pk = sk.public_key
            public_key_to_owner[bytes(pk)] = secret_key_to_owner[bytes(sk)]
            key_mapping[bytes(sk)] = bytes(pk)
            key_mapping[bytes(pk)] = bytes(sk)
        else:
            self._sk = secret_key

    @property
    def public_key(self) -> bytes:
        pk = self._sk.public_key
        return bytes(pk)

    def encrypt_and_auth(self, data: bytes, friend_pk: bytes):
        if type(data) is not bytes:
            raise TypeError("data must be bytes")
        friend_pk = PublicKey(friend_pk)
        if DEBUG:
            print(
                f"AuthEnc encrypting {data} for {friend_pk} (from pk {self.public_key})"
            )
        return Lab3EncAndAuth(bytes(friend_pk), bytes(self._sk), data)

    def decrypt_and_verify(self, ciphertext: bytes, friend_pk: bytes) -> bytes:
        return Lab3DecAndVer(bytes(self._sk), bytes(friend_pk), ciphertext)

