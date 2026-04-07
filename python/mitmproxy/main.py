#!/usr/bin/env python3

import atexit
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parent
ADDON = ROOT / "addon.py"


def get_env(name: str, default: str) -> str:
    value = os.getenv(name, default)
    return value.strip() if isinstance(value, str) else default


def wait_for_port(host: str, port: int, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError(f"Timed out waiting for {host}:{port}")


def main() -> int:
    upstream_host = get_env("PROXY_HOST", "127.0.0.1")
    upstream_port = get_env("PROXY_PORT", "31111")
    user = get_env("PROXY_USERNAME", get_env("PROXY_USER", "user"))
    password = get_env("PROXY_PASSWORD", get_env("PROXY_PASS", "password"))
    target = get_env("TARGET_URL", "http://httpbin.org/ip")
    listen_host = "127.0.0.1"
    listen_port = int(get_env("MITMPROXY_PORT", "38080"))
    tunnel_seed = get_env("PROXY_TUNNEL", "python-mitmproxy-demo")

    env = dict(os.environ)
    env["PROXY_TUNNEL"] = tunnel_seed

    cmd = [
        "mitmdump",
        "--listen-host",
        listen_host,
        "--listen-port",
        str(listen_port),
        "--mode",
        f"upstream:http://{upstream_host}:{upstream_port}",
        "--upstream-auth",
        f"{user}:{password}",
        "-s",
        str(ADDON),
        "--set",
        "connection_strategy=lazy",
    ]

    proc = subprocess.Popen(cmd, cwd=ROOT, env=env)

    def cleanup() -> None:
        if proc.poll() is None:
            proc.send_signal(signal.SIGTERM)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    atexit.register(cleanup)

    wait_for_port(listen_host, listen_port)

    session = requests.Session()
    session.proxies = {
        "http": f"http://{listen_host}:{listen_port}",
        "https": f"http://{listen_host}:{listen_port}",
    }

    for index in range(1, 4):
        response = session.get(target, timeout=30)
        response.raise_for_status()
        print(f"请求 {index}: {response.status_code} - {response.text.strip()}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        sys.exit(130)
