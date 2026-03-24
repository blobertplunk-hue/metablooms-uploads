#!/usr/bin/env python3
"""
receive_uploads.py — HTTP upload receiver for MetaBlooms repo.

Listens on 0.0.0.0:8765, accepts POST /upload (multipart/form-data),
saves files to DEST_DIR, prints SHA256 receipt per file.
Exits cleanly after receiving EXPECTED_FILES files, or on SIGINT (Ctrl-C).

Usage:
    python3 scripts/receive_uploads.py
"""

import hashlib
import http.server
import io
import os
import signal
import socket
import sys

# ── config ────────────────────────────────────────────────────────────────────
PORT = 8765
DEST_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root
EXPECTED_FILES = 2

# ── state ─────────────────────────────────────────────────────────────────────
received: list[str] = []


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_multipart(data: bytes, boundary: bytes) -> list[tuple[str, bytes]]:
    """Return list of (filename, content) tuples from a multipart body."""
    results = []
    delimiter = b"--" + boundary
    parts = data.split(delimiter)
    for part in parts[1:]:  # skip preamble
        if part in (b"--\r\n", b"--"):
            break
        # split headers from body
        if b"\r\n\r\n" not in part:
            continue
        headers_raw, body = part.split(b"\r\n\r\n", 1)
        body = body.rstrip(b"\r\n")
        # extract filename from Content-Disposition
        filename = None
        for line in headers_raw.split(b"\r\n"):
            if b"Content-Disposition" in line:
                for token in line.split(b";"):
                    token = token.strip()
                    if token.startswith(b"filename="):
                        filename = token[9:].strip(b'"').decode("utf-8", errors="replace")
        if filename:
            results.append((filename, body))
    return results


class UploadHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # suppress default access log
        pass

    def send_text(self, code: int, msg: str):
        body = msg.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self.send_text(200, "ok\n")
        else:
            self.send_text(404, "not found\n")

    def do_POST(self):
        if self.path != "/upload":
            self.send_text(404, "POST to /upload\n")
            return

        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self.send_text(400, "Expected multipart/form-data\n")
            return

        # extract boundary
        boundary = None
        for part in content_type.split(";"):
            part = part.strip()
            if part.startswith("boundary="):
                boundary = part[9:].strip('"').encode()
        if not boundary:
            self.send_text(400, "Missing boundary\n")
            return

        length = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(length)
        files = parse_multipart(data, boundary)

        if not files:
            self.send_text(400, "No files found in upload\n")
            return

        responses = []
        for filename, content in files:
            dest = os.path.join(DEST_DIR, os.path.basename(filename))
            with open(dest, "wb") as f:
                f.write(content)
            digest = sha256_of(dest)
            received.append(filename)
            line = f"✓ {filename}  sha256={digest}"
            print(line, flush=True)
            responses.append(line)

        self.send_text(200, "\n".join(responses) + "\n")

        if len(received) >= EXPECTED_FILES:
            print(f"\nAll {EXPECTED_FILES} files received. Shutting down.", flush=True)
            # schedule shutdown after response is sent
            signal.raise_signal(signal.SIGTERM)


def get_local_ips() -> list[str]:
    ips = []
    try:
        hostname = socket.gethostname()
        ips = socket.gethostbyname_ex(hostname)[2]
        ips = [ip for ip in ips if not ip.startswith("127.")]
    except Exception:
        pass
    if not ips:
        # fallback: connect to a public IP to discover outbound interface
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                ips = [s.getsockname()[0]]
        except Exception:
            ips = ["<unknown>"]
    return ips


def main():
    ips = get_local_ips()
    print("=" * 60)
    print(f"  MetaBlooms upload receiver  —  port {PORT}")
    print("=" * 60)
    print(f"  Saving files to: {DEST_DIR}")
    print(f"  Waiting for {EXPECTED_FILES} file(s)...\n")
    print("  Run this in Termux:")
    for ip in ips:
        print(f"    bash termux_upload.sh {ip}")
    print()

    server = http.server.HTTPServer(("0.0.0.0", PORT), UploadHandler)

    def _shutdown(sig, frame):
        print("\nShutting down receiver.", flush=True)
        # run in thread to avoid blocking the signal handler
        import threading
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    try:
        server.serve_forever()
    except Exception:
        pass


if __name__ == "__main__":
    main()
