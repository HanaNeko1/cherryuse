"""Read-only local image server for inline image display in chat.

Serves image files from --root over http://127.0.0.1:<port>/.
- Loopback only: unreachable from other machines
- Only image extensions are served; directory listing is disabled
- GET /_ping returns "ok|<abs-root>" for health checks

Usage:
    python imgserver.py --root "C:\\path\\to\\images" --port 18080
"""

import argparse
import http.server
import os
import socketserver

ALLOWED = {".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif"}


def build_handler(root):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=root, **kwargs)

        def list_directory(self, path):
            self.send_error(403, "Directory listing disabled")
            return None

        def do_GET(self):
            if self.path == "/_ping":
                body = f"ok|{root}".encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            ext = os.path.splitext(self.path.split("?")[0])[1].lower()
            if ext not in ALLOWED:
                self.send_error(404, "Only image files are served")
                return
            super().do_GET()

        def log_message(self, *args):
            pass

    return Handler


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="directory to serve")
    ap.add_argument("--port", type=int, default=18080)
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        raise SystemExit(f"not a directory: {root}")

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", args.port), build_handler(root)) as httpd:
        print(f"serving {root} on http://127.0.0.1:{args.port}/", flush=True)
        httpd.serve_forever()


if __name__ == "__main__":
    main()
