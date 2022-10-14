"""
Test fixtures that are compatible with the crypto overrides
"""

import typing as t
from common.errors import SynchronizationError

from server.reference_server import InMemoryStorage, ReferenceServer
from server.spec import Server
import common.types as types
import common.errors as errors
from ag.common.testing import test_case
from ag.common.mock_http import link_client_server

from . import crypto_overrides as co

from client import client

def new_client(server: Server, username: str) -> client.Client:
    """
    Creates but does not register a new client
    """
    co.current_owner = username
    c = client.Client(username)
    link_client_server(c, server)
    return c

def new_registered_client(server: Server, username: str) -> client.Client:
    """
    Creates a registers a new client. Returns the client
    """
    c = new_client(server, username)
    c.register()
    return c

def three_clients(server: Server) -> t.Tuple[client.Client, client.Client, client.Client]:
    """
    Creates three clients "alice", "bob", and "carlos" and registers them with the server.

    Returns the three clients

    Does not post photos.
    """

    alice = new_registered_client(server, "alice")
    bob = new_registered_client(server, "bob")
    carlos = new_registered_client(server, "carlos")

    return alice, bob, carlos

def two_clients(server: Server) -> t.Tuple[client.Client, client.Client]:
    """
    Creates two clients "alice" and "bob", registers them with the given server,
    and posts one photo from each.

    Returns the two clients

    Does not upload photos for the clients
    """

    alice = new_registered_client(server, "alice")
    bob = new_registered_client(server, "bob")

    return alice, bob
