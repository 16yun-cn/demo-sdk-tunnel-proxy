import os
from mitmproxy import http

HOST = os.getenv("PROXY_HOST", "t.16yun.cn")
PORT = os.getenv("PROXY_PORT", "31111")
# Canonical with alias fallback
USER = os.getenv("PROXY_USERNAME") or os.getenv("PROXY_USER") or "username"
PASS = os.getenv("PROXY_PASSWORD") or os.getenv("PROXY_PASS") or "password"
SEED = os.getenv("TUNNEL_SEED", "1")

class UpstreamProxy:
    def request(self, flow: http.HTTPFlow) -> None:
        # 注入 Proxy-Tunnel 普通请求头
        flow.request.headers.setdefault("Proxy-Tunnel", SEED)

    def configure(self, updates):
        pass

addons = [UpstreamProxy()]

# 以环境变量启动 mitmproxy 并传入上游代理:
# mitmproxy --mode upstream:http://username:password@t.16yun.cn:31111 -s addon.py
