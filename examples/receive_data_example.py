"""
OAuth2 client_credentials authentication + data receiving demo

Flow:
    1. Client sends grant_type / client_id / client_secret to /api/oauth/token to obtain an access_token
    2. Client pushes data to /api/receive/data with Authorization: Bearer <access_token>
"""
import json
import secrets
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs


# Mock client registry: client_id -> client_secret (use a database or config center in real projects)
CLIENTS = {
    "demo-client": "demo-secret",
}

# In-memory token store: access_token -> {"client_id": ..., "expires_at": ...}
TOKENS = {}

TOKEN_TTL = 3600  # token lifetime in seconds


def issue_token(client_id):
    """Generate a random token and record its expiration."""
    token = secrets.token_hex(16)
    TOKENS[token] = {"client_id": client_id, "expires_at": time.time() + TOKEN_TTL}
    return token


def verify_token(authorization):
    """Parse the Bearer token from the Authorization header and return client_id; None if invalid."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    record = TOKENS.get(authorization[len("Bearer "):])
    if not record or record["expires_at"] < time.time():
        return None
    return record["client_id"]


def read_body(handler):
    """Read the request body, supporting both application/json and application/x-www-form-urlencoded."""
    length = int(handler.headers.get("Content-Length", 0))
    raw = handler.rfile.read(length).decode("utf-8") if length else ""
    ctype = handler.headers.get("Content-Type", "")
    if "application/json" in ctype:
        return json.loads(raw or "{}")
    return {k: v[0] for k, v in parse_qs(raw).items()}


def send_json(handler, status, payload):
    """Send a unified JSON response."""
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class PostHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/api/oauth/token":
            self.handle_token()
        elif self.path == "/api/receive/data":
            self.handle_receive()
        else:
            send_json(self, 404, {"error": "not_found"})

    def handle_token(self):
        """OAuth2 client_credentials token endpoint."""
        form = read_body(self)
        grant_type = form.get("grant_type")
        client_id = form.get("client_id")
        client_secret = form.get("client_secret")

        if grant_type != "client_credentials":
            send_json(self, 400, {"error": "unsupported_grant_type"})
            return
        if CLIENTS.get(client_id) != client_secret:
            send_json(self, 401, {"error": "invalid_client"})
            return

        send_json(self, 200, {
            "access_token": issue_token(client_id),
            "token_type": "Bearer",
            "expires_in": TOKEN_TTL,
        })

    def handle_receive(self):
        """Protected endpoint: must pass Bearer token validation first."""
        client_id = verify_token(self.headers.get("Authorization"))
        if not client_id:
            send_json(self, 401, {"error": "invalid_token"})
            return

        try:
            data = read_body(self)
        except json.JSONDecodeError:
            send_json(self, 400, {"error": "invalid_json"})
            return

        print(f"[{client_id}] received data: {data}")
        send_json(self, 200, {"status": "success", "received": True})


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 9001), PostHandler)
    print("Server running on port 9001...")
    server.serve_forever()


# ------- Usage examples -------
# 1) Obtain a token
# curl -X POST http://127.0.0.1:9001/api/oauth/token \
#      -H 'Content-Type: application/x-www-form-urlencoded' \
#      -d 'grant_type=client_credentials&client_id=demo-client&client_secret=demo-secret'
#
# 2) Push data with the token
# curl -X POST http://127.0.0.1:9001/api/receive/data \
#      -H 'Content-Type: application/json' \
#      -H 'Authorization: Bearer <access_token from step 1>' \
#      -d '{"hello":"world"}'
