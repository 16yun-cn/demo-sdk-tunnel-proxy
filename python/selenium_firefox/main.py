#!/usr/bin/env python3
"""
Selenium Firefox + 16YUN 隧道代理（用户名/密码，selenium-wire）
"""

import os
from typing import Optional

from seleniumwire import webdriver  # type: ignore
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name, default)
    return v.strip() if isinstance(v, str) else v


def install_geckodriver() -> str:
    driver_path = get_env("GECKODRIVER_PATH")
    if driver_path:
        return driver_path

    for candidate in ("/usr/bin/geckodriver", "/usr/local/bin/geckodriver"):
        if os.path.exists(candidate):
            return candidate

    system_ca_bundle = "/etc/ssl/certs/ca-certificates.crt"
    overrides = {}
    if os.path.exists(system_ca_bundle):
        for key in ("REQUESTS_CA_BUNDLE", "SSL_CERT_FILE", "CURL_CA_BUNDLE"):
            overrides[key] = system_ca_bundle
    previous = {key: os.environ.get(key) for key in overrides}
    os.environ.update(overrides)
    try:
        return GeckoDriverManager().install()
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def main() -> int:
    host = get_env("PROXY_HOST", "t.16yun.cn")
    port = get_env("PROXY_PORT", "31111")
    shim_enabled = get_env("TUNNEL_BROWSER_PROXY_SHIM", "0") == "1"
    # Canonical with alias fallback
    user = get_env("PROXY_USERNAME", "user") or get_env("PROXY_USER", "user")
    pwd = get_env("PROXY_PASSWORD") or get_env("PROXY_PASS")
    if not (host and port and ((shim_enabled) or (user and pwd))):
        print("请设置 PROXY_HOST/PROXY_PORT/PROXY_USERNAME/PROXY_PASSWORD")
        return 2

    seleniumwire_options = {
        "proxy": {
            "http": f"http://{host}:{port}" if shim_enabled else f"http://{user}:{pwd}@{host}:{port}",
            "https": f"http://{host}:{port}" if shim_enabled else f"http://{user}:{pwd}@{host}:{port}",
        }
    }
    
    options = Options()
    options.add_argument("--headless")
    
    service = Service(executable_path=install_geckodriver())
    
    driver = webdriver.Firefox(service=service, options=options, seleniumwire_options=seleniumwire_options)
    try:
        # 使用 HTTP 避免证书问题
        driver.get(get_env("TARGET_URL", "http://httpbin.org/ip"))
        print(driver.page_source[:500])
    finally:
        driver.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
