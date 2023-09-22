import http.server
import json
import socketserver
import threading
from typing import Callable


class MockRequestHandler(http.server.SimpleHTTPRequestHandler):
    # class MockRequestHandler(http.server.CGIHTTPRequestHandler):
    def __init__(self, *args, responses=None, requests=[], **kwargs):
        self.response_sequences = responses
        self.requests = requests
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        """Suppress logging to stdout."""
        pass

    def do_GET(self):
        status = 404
        response = {}
        if self.path in self.response_sequences:
            responses = self.response_sequences[self.path]
            if responses:
                print(f"<< pop {self.path}")
                status, response = responses.pop(0)
            self.requests.append((self.command, self.path, response))
        else:
            raise Exception(f"Unexpected path: {self.path}")

        self.send_response(status)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        if response:
            self.wfile.write(json.dumps(response).encode())


class MockServer(socketserver.TCPServer):
    allow_reuse_address = True
    """I think this implements socket.SO_REUSEADDR, which allows the server to restart without waiting for a TIME_WAIT to expire from a previous run of the code that left a socket dangling (in a separate process). Otherwise back-to-back server starts can fail with "socket already in use" error."""


def start_test_server(
    create_request_handler: Callable[..., http.server.BaseHTTPRequestHandler]
):
    host = "localhost"
    port = 4444
    address = f"http://{host}:{port}"
    httpd = MockServer((host, port), create_request_handler)
    httpd_thread = threading.Thread(target=httpd.serve_forever)
    httpd_thread.daemon = True
    httpd_thread.start()
    return address, httpd, httpd_thread


class MockServerSession:
    """Use this in tests to start a test server and shut it down when the test is done.

    Example:

    def create_request_handler(*args, **kwargs):
        ...
        return MockRequestHandler(*args, **kwargs, responses=response_sequences)

    with TestServerSession(create_request_handler):
        ...
    """

    __test__ = False
    """Stop pytest trying to "collect" this class as a test."""

    def __init__(
        self, create_request_handler: Callable[..., http.server.BaseHTTPRequestHandler]
    ):
        self.create_request_handler = create_request_handler

    def __enter__(self):
        self.address, self.httpd, self.httpd_thread = start_test_server(
            self.create_request_handler
        )
        return self.address

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.httpd.shutdown()
        self.httpd_thread.join()


if __name__ == "__main__":
    # To test this server in the terminal, run:
    httpd, httpd_thread = start_test_server()
    httpd_thread.join()
