import copy
import typing as t

if t.TYPE_CHECKING:
    from client.client import Client
    from server.spec import Server
from server.app import map_rpc_type
import common.types as types


def link_client_server(client_instance: "Client", server: "Server") -> None:
    """
    Overrides the send_rpc method in the client
    to call the server directly, without the need for
    an HTTP server.
    """

    def send_rpc_mocked(self, request: types.RpcObject) -> types.RpcObject:
        # "client" - sending request
        serialized = copy.deepcopy(request.as_rpc_dict())

        # "server" - handling
        rpc_type_str = serialized.get("rpc")
        rpc_data = serialized.get("data")

        rpc_type, server_method = map_rpc_type(server, rpc_type_str)
        rpc = rpc_type.from_dict(rpc_data)
        # call the function corresponding to this RPC
        response = server_method(rpc).as_rpc_dict()

        # "client" - receiving response
        resp_type = self.RESPONSE_MAPPINGS.get(response["rpc"], None)
        if resp_type is None:
            raise ValueError(f'Invalid response type "{response["rpc"]}".')
        resp = resp_type.from_dict(response["data"])
        return copy.deepcopy(resp)

    client_instance.send_rpc = send_rpc_mocked.__get__(
        client_instance, type(client_instance)
    )

