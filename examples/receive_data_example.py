from http.server import BaseHTTPRequestHandler, HTTPServer
import json



class PostHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/receive/data':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode('utf-8'))
                print(f"Received data: {data}")
                response = {"status": "success", "received": True}
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Invalid JSON')
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                response = {"status": "fail", "received": False}
                self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 9001), PostHandler)
    print("Server running on port 9001...")
    server.serve_forever()


    """
curl --location 'http://127.0.0.1:9001/api/receive/data' \
--header 'Content-Type: application/json' \
--data '{
 
}'
    """
