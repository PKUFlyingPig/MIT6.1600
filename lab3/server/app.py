# This file is responsible for taking HTTP requests and passing them
# on to the Server class.

from flask import Flask, request, jsonify
import common.types as types
from server.reference_server import ReferenceServer
from server.spec import Server
import typing as t


def map_rpc_type(server: Server, rpc_type: str):
    # maps RPC name to request type and corresponding function
    RPC_REQUEST_MAPPING: t.Dict[
        str, t.Tuple[types.RpcObject, t.Callable[[types.RpcObject], types.RpcObject]]
    ] = {
        "LoginRequest": (types.LoginRequest, server.login),
        "RegisterRequest": (types.RegisterRequest, server.register_user),
        "UpdatePublicProfileRequest": (
            types.UpdatePublicProfileRequest,
            server.update_public_profile,
        ),
        "GetFriendPublicProfileRequest": (
            types.GetFriendPublicProfileRequest,
            server.get_friend_public_profile,
        ),
        "PutPhotoRequest": (types.PutPhotoRequest, server.put_photo_user),
        "GetPhotoRequest": (types.GetPhotoRequest, server.get_photo_user),
        "SynchronizeRequest": (types.SynchronizeRequest, server.synchronize),
        "SynchronizeFriendRequest": (
            types.SynchronizeFriendRequest,
            server.synchronize_friend,
        ),
        "PushLogEntryRequest": (types.PushLogEntryRequest, server.push_log_entry),
        "GetAlbumRequest": (types.GetAlbumRequest, server.get_album),
        "UploadAlbumRequest": (types.UploadAlbumRequest, server.upload_album),
    }
    return RPC_REQUEST_MAPPING[rpc_type]


def create_app(server_instance: t.Optional[Server] = None):
    """
    Creates and returns a flask app to interface with the server.

    Uses a server implementation of the given type. If no implementation
    is given, uses the reference server.
    """
    if server_instance is None:
        server_instance = ReferenceServer()

    app = Flask(__name__)

    @app.route("/rpc", methods=["POST"])
    def handle_rpc():
        body = request.get_json()
        print()
        print("got RPC request!")
        print(body)
        rpc_type_str = body.get("rpc")
        rpc_data = body.get("data")

        rpc_type, server_method = map_rpc_type(server_instance, rpc_type_str)
        rpc = rpc_type.from_dict(rpc_data)
        print("deserialized into", rpc)
        # call the function corresponding to this RPC
        response_data = server_method(rpc)
        print("responding with", response_data)
        return jsonify(response_data.as_rpc_dict())

    return app

