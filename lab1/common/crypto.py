#!/usr/bin/env python3

import secrets
import hmac
import hashlib
from nacl.signing import SigningKey, VerifyKey
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

    def get_secret(self) -> bytes:
        return self._secret

    def get_auth_secret(self) -> bytes:
        return self._auth_secret

    def get_symmetric_key(self) -> bytes:
        return self._symmetric_key



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



