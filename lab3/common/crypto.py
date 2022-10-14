#!/usr/bin/env python3

import secrets
import hmac
import hashlib
from nacl.signing import SigningKey, VerifyKey
from nacl.public import PrivateKey, PublicKey, Box
from nacl.secret import SecretBox
from nacl.utils import random
import nacl
import typing as t

import common.codec as codec

# TODO check public key encoding

hash_function = hashlib.sha3_256


class UserSecret:
    """A user secret used for key generation."""

    def __init__(self, secret: bytes = None):
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

    def _generate_auth_secret(self) -> bytes:
        h_ctxt = hash_function()
        h_ctxt.update("auth_secret".encode("utf-8"))
        h_ctxt.update(self._secret)
        return h_ctxt.digest()

    def _generate_symmetric_key(self) -> bytes:
        h_ctxt = hash_function()
        h_ctxt.update("symmetric_key".encode("utf-8"))
        h_ctxt.update(self._secret)
        return h_ctxt.digest()

    def _generate_signing_key_pair(self) -> t.Tuple[SigningKey, bytes]:
        h_ctxt = hash_function()
        h_ctxt.update("signing_key_pair".encode("utf-8"))
        h_ctxt.update(self._secret)
        seed_sk = h_ctxt.digest()
        sk = SigningKey(seed_sk)
        pk = sk.verify_key
        return (sk, pk)

    def _generate_encrypt_and_auth_key_pair(self) -> t.Tuple[PrivateKey, bytes]:
        h_ctxt = hash_function()
        h_ctxt.update("encrypt_and_auth_key_pair".encode("utf-8"))
        h_ctxt.update(self._secret)
        seed_sk = h_ctxt.digest()
        sk = PrivateKey(seed_sk)  # TODO this might be insecure
        pk = sk.public_key
        return (sk, pk)

    def get_secret(self) -> bytes:
        return self._secret

    def get_auth_secret(self) -> bytes:
        return self._auth_secret

    def get_symmetric_key(self) -> bytes:
        return self._symmetric_key

    def get_signing_public_key(self):
        return self._s_pk

    def get_signing_secret_key(self):
        return self._s_sk

    def get_encrypt_and_auth_public_key(self):
        return self._e_pk

    def get_encrypt_and_auth_secret_key(self):
        return self._e_sk


class MessageAuthenticationCode:
    """A wrapper for symmetric keys to produce message authentication codes."""

    def __init__(self, symmetric_key: bytes = None):
        """Wrap the given symmetric key.

        If none is provided, generate a new key.

        >>> prover = MessageAuthenticationCode()
        """
        if symmetric_key == None:
            self._secret_key = secrets.token_bytes(256)
        else:
            self._secret_key = symmetric_key

    def gen_mac(self, data):
        """Create a message authenticator over the data given the
        symmetric key.

        >>> prover = MessageAuthenticationCode("fake_secret_key".encode('utf-8'))
        >>> payload = codec.encode([b"Hello ", "Security!", 1])
        >>> prover.gen_mac(payload).hex()
        'ea26559534068e55b1e64e920bbb8a136cfcb838d07ffd37a24b2e0a19513e6f'
        """
        if type(data) is not bytes:
            raise TypeError("data must be a bytes encoding")
        return hmac.new(self._secret_key, data, hash_function).digest()

    def compare_mac(self, data, auth):
        """Check the provided message authenticator against the given
        data and secret.

        >>> prover = MessageAuthenticationCode("fake_secret_key".encode('utf-8'))

        >>> payload = codec.encode([b"Hello ", "Security!", 1])
        >>> mac = prover.gen_mac(payload)
        >>> prover.compare_mac(payload, mac)
        True
        """
        if type(data) is not bytes:
            raise TypeError("data must be a bytes encoding")
        return hmac.compare_digest(
            hmac.new(self._secret_key, data, hash_function).digest(), auth
        )


def data_hash(data):
    """Encode and hash the given data.

    >>> data_hash([9, 4, 4, 3, 2, 1]).hex()
    '6a64753d3acc5556bf3c35f3dd57187be688819c8a5aa40f48521ddbc70a9f84'
    """
    h_ctxt = hash_function()
    h_ctxt.update(codec.encode(data))
    return h_ctxt.digest()


def verify_data_hash(data, output):
    """Verify that the given data corresponds to the given hash output.

    >>> hex = '6a64753d3acc5556bf3c35f3dd57187be688819c8a5aa40f48521ddbc70a9f84'
    >>> expect = bytes.fromhex(hex)
    >>> verify_data_hash([9, 4, 4, 3, 2, 1], expect)
    True
    """
    h = data_hash(data)
    return h == output


class PublicKeySignature:
    def __init__(self, secret_key: SigningKey = None):
        """Save the key pair.
        If none is provided, generate a new key pair.

        >>> prover = PublicKeySignature()
        """
        if secret_key == None:
            self._sk = SigningKey.generate()
            self._pk = self._sk.verify_key
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
            raise TypeError("data must be a bytes encoding")
        return self._sk.sign(data).signature


def verify_sign(pk: bytes, data: bytes, signature: bytes) -> bool:
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
    verify_key = VerifyKey(pk)
    try:
        ret = verify_key.verify(data, signature) == data
    except nacl.exceptions.BadSignatureError:
        return False
    return ret


def generate_symmetric_secret_key():
    return random(SecretBox.KEY_SIZE)


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
        else:
            self._sk = secret_key
        self.box = SecretBox(self._sk)

    def encrypt(self, data: bytes) -> bytes:
        return bytes(self.box.encrypt(data))

    def decrypt(self, ciphertext: bytes) -> bytes:
        return self.box.decrypt(ciphertext)


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
            self._sk = PrivateKey.generate()
        else:
            self._sk = secret_key

    @property
    def public_key(self) -> bytes:
        return bytes(self._sk.public_key)

    def encrypt_and_auth(self, data: bytes, friend_pk: bytes) -> bytes:
        friend_pk = PublicKey(friend_pk)
        box = Box(self._sk, friend_pk)
        return bytes(box.encrypt(data))

    def decrypt_and_verify(self, ciphertext: bytes, friend_pk: bytes) -> bytes:
        friend_pk = PublicKey(friend_pk)
        box = Box(self._sk, friend_pk)
        return box.decrypt(ciphertext)

