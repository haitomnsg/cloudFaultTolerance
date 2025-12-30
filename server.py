from http.server import BaseHTTPRequestHandler, HTTPServer
import socket
import os
from urllib.parse import urlparse, parse_qs

ACTIVE = True


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global ACTIVE

        server_name = os.environ.get("SERVER_NAME", socket.gethostname())
        parsed = urlparse(self.path)

        # Control endpoint: toggle this server as active/inactive
        if parsed.path == "/control/toggle":
            params = parse_qs(parsed.query)
            target = params.get("target", [None])[0]
            active_param = params.get("active", [None])[0]

            # Only the matching server updates its state
            if target == server_name and active_param is not None:
                ACTIVE = active_param.lower() == "true"
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                state = "active" if ACTIVE else "inactive"
                self.wfile.write(
                    f"STATUS UPDATED: server {server_name} is now {state}\n".encode()
                )
            else:
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(
                    f"IGNORED: control call for {target}, I am {server_name}\n".encode()
                )
            return

        # Main API endpoint: if inactive, simulate failure so Nginx routes around it
        if parsed.path.startswith("/api"):
            if not ACTIVE:
                self.send_response(503)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(
                    f"Server {server_name} is marked INACTIVE, simulating failure.\n".encode()
                )
                return

            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(
                f"Response from server: {server_name}\n".encode()
            )
            return

        # Fallback for any other path
        self.send_response(404)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Not Found\n")

server = HTTPServer(("0.0.0.0", 5000), Handler)
server.serve_forever()
