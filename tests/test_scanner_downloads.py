"""Exercise the workflow's curl commands against real local receive failures."""

import os
import re
import shutil
import socket
import socketserver
import struct
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CURL = shutil.which("curl")


def download_commands():
    lines = (ROOT / ".github/workflows/tests-and-plugin-integrity.yml").read_text().splitlines()
    step = lines.index("      - name: Install and verify pinned secret scanners")
    start = lines.index("        run: |", step) + 1
    commands, current = [], []
    for line in lines[start:]:
        if line.strip() and not line.startswith("          "):
            break
        line = line[10:]
        if line.startswith("curl ") or current:
            current.append(line)
            if not line.rstrip().endswith("\\"):
                commands.append("\n".join(current))
                current = []
    if len(commands) != 2 or current:
        raise ValueError("Expected both complete scanner download commands")
    return commands


class DownloadServer(socketserver.TCPServer):
    allow_reuse_address = True

    def shutdown_request(self, request):
        # A graceful shutdown would turn the intended reset into an empty reply.
        self.close_request(request)


class DownloadHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.request.settimeout(5)
        headers = b""
        while b"\r\n\r\n" not in headers:
            chunk = self.request.recv(4096)
            if not chunk:
                return
            headers += chunk
        self.server.requests += 1
        if self.server.failures is None or self.server.requests <= self.server.failures:
            self.request.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
            return
        body = b"synthetic scanner archive"
        self.request.sendall(
            b"HTTP/1.1 200 OK\r\nContent-Length: " + str(len(body)).encode()
            + b"\r\nConnection: close\r\n\r\n" + body
        )


@unittest.skipUnless(CURL, "curl is required for workflow download tests")
class ScannerDownloadTests(unittest.TestCase):
    def run_download(self, command, failures):
        with DownloadServer(("127.0.0.1", 0), DownloadHandler) as server, tempfile.TemporaryDirectory() as tmp:
            server.failures, server.requests = failures, 0
            thread = threading.Thread(
                target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True
            )
            thread.start()
            try:
                output = Path(tmp) / "scanner.tar.gz"
                url = f"http://127.0.0.1:{server.server_address[1]}/scanner.tar.gz"
                command = re.sub(r"https://[^\s\\]+", url, command)
                env = {**os.environ, "NO_PROXY": "*", "no_proxy": "*",
                       "gitleaks_archive": str(output), "trufflehog_archive": str(output)}
                result = subprocess.run(
                    ["bash", "-c", "set -euo pipefail\n" + command],
                    env=env, capture_output=True, text=True, timeout=20,
                )
                return result, server.requests, output.read_bytes() if output.exists() else b""
            finally:
                server.shutdown()
                thread.join(timeout=5)

    def test_each_scanner_download_recovers_from_receive_failure(self):
        for index, command in enumerate(download_commands()):
            with self.subTest(scanner=index):
                result, requests, body = self.run_download(command, failures=1)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(requests, 2)
                self.assertEqual(body, b"synthetic scanner archive")

    def test_each_scanner_download_fails_after_bounded_retries(self):
        for index, command in enumerate(download_commands()):
            with self.subTest(scanner=index):
                result, requests, _ = self.run_download(command, failures=None)
                self.assertEqual(result.returncode, 56, result.stderr)
                self.assertEqual(requests, 4)


if __name__ == "__main__":
    unittest.main()
