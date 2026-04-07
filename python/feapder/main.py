#!/usr/bin/env python3
"""
16YUN(亿牛云) 隧道代理（feapder 版）
"""

import os
from typing import Optional

import feapder


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name, default)
    return v.strip() if isinstance(v, str) else v


class DemoSpider(feapder.AirSpider):
    def start_requests(self):  # type: ignore[override]
        yield feapder.Request("https://httpbin.org/ip")

    def download_midware(self, request):  # type: ignore[override]
        host = get_env("PROXY_HOST", "t.16yun.cn")
        port = get_env("PROXY_PORT", "31111")
        # Canonical with alias fallback
        user = get_env("PROXY_USERNAME", "user") or get_env("PROXY_USER", "user")
        pwd = get_env("PROXY_PASSWORD") or get_env("PROXY_PASS")

        if user and pwd:
            proxy = f"http://{user}:{pwd}@{host}:{port}"
        else:
            proxy = f"http://{host}:{port}"
        request.proxies = {"http": proxy, "https": proxy}
        return request

    def parse(self, request, response):  # type: ignore[override]
        print(response.text)


if __name__ == "__main__":
    DemoSpider().start()

