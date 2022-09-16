import typing as t
import contextlib
from multiprocessing import Process

from server.spec import Server
import server.app as app

@contextlib.contextmanager
def run_server(server_type: t.Type[Server]):
    """
    Run the given server implementation in the background.

    This should be used a context manager, like the following:

    ```
    with run_server() as (server_url, server):
        client = Client("username", server_url)
        ...
    ```

    Note that the server's url (eg http://127.0.0.1:5000) is returned
    along with the actual server object (to be manipulated in test cases)
    The server will automatically be torn down at the end of the context.
    """
    SERVER_HOSTNAME = "127.0.0.1"
    SERVER_PORT = 5000

    server = server_type()
    server_app = app.create_app(server)
    # run the server in another process
    p = Process(target=server_app.run, args=(SERVER_HOSTNAME, SERVER_PORT))
    p.start()
    yield f"http://{SERVER_HOSTNAME}:{SERVER_PORT}", server
    p.terminate()
