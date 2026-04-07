#!/usr/bin/env python3

import atexit
import json
import os
import signal
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests


ROOT = Path(__file__).resolve().parent


class SplashHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/execute":
            self.send_error(404)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length).decode("utf-8")
        params = parse_qs(raw_body)
        target_url = params.get("url", [os.getenv("TARGET_URL", "http://httpbin.org/ip")])[0]
        tunnel_seed = os.getenv("PROXY_TUNNEL", "python-scrapy-splash-demo")

        proxy_headers = {}
        if tunnel_seed:
            proxy_headers["Proxy-Tunnel"] = tunnel_seed

        proxy_host = os.getenv("PROXY_HOST", "127.0.0.1")
        proxy_port = os.getenv("PROXY_PORT", "31111")
        proxy_user = os.getenv("PROXY_USERNAME") or os.getenv("PROXY_USER") or "user"
        proxy_pass = os.getenv("PROXY_PASSWORD") or os.getenv("PROXY_PASS") or "password"
        proxy = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"

        response = requests.get(
            target_url,
            headers=proxy_headers,
            proxies={"http": proxy, "https": proxy},
            timeout=30,
            verify=os.getenv("REQUESTS_CA_BUNDLE"),
        )
        response.raise_for_status()

        body = response.text
        payload = {
            "url": target_url,
            "http_status": response.status_code,
            "html": body,
            "headers": dict(response.headers),
        }

        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def run_fake_splash(port: int) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", port), SplashHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def main() -> int:
    splash_port = int(os.getenv("SPLASH_PORT", "8050"))
    server = run_fake_splash(splash_port)
    atexit.register(server.shutdown)

    cmd = ["scrapy", "crawl", "httpbin"]
    proc = subprocess.run(cmd, cwd=ROOT, text=True)
    return proc.returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        sys.exit(130)
