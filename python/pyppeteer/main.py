#!/usr/bin/env python3
"""
16YUN(亿牛云) 隧道代理（pyppeteer 版）
"""

import asyncio
import os
from typing import Optional

from pyppeteer import launch


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name, default)
    return v.strip() if isinstance(v, str) else v


def resolve_chrome_path() -> str:
    configured = get_env("CHROME_BIN")
    if configured:
        return configured

    for candidate in ("/usr/bin/chromium", "/usr/bin/google-chrome-stable"):
        if os.path.exists(candidate):
            return candidate

    return "/usr/bin/google-chrome-stable"


async def main() -> None:
    host = get_env("PROXY_HOST", "t.16yun.cn")
    port = get_env("PROXY_PORT", "31111")
    user = get_env("PROXY_USERNAME", "user") or get_env("PROXY_USER", "user")
    pwd = get_env("PROXY_PASSWORD") or get_env("PROXY_PASS")
    target = get_env("TARGET_URL", "http://httpbin.org/ip")
    chrome_path = resolve_chrome_path()

    browser = await launch(
        {
            "headless": True,
            "executablePath": chrome_path,
            "ignoreHTTPSErrors": True,
            "args": [
                f"--proxy-server=http://{host}:{port}",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--ignore-certificate-errors",
            ],
        }
    )
    page = await browser.newPage()
    page.on("request", lambda req: print(f">> {req.method} {req.url}"))
    page.on("response", lambda res: print(f"<< {res.status} {res.url}"))
    if user and pwd:
        await page.authenticate({"username": user, "password": pwd})
    try:
        print(f"Browser executable: {chrome_path}")
        print(f"Target URL: {target}")
        await page.goto(target, {"waitUntil": "domcontentloaded", "timeout": 60000})
        html = await page.content()
        print(html[:500])
    finally:
        await browser.close()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
