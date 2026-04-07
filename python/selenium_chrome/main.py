#!/usr/bin/env python3
"""
Selenium Chrome + 16YUN 隧道代理（用户名/密码）
"""

import os
import string
import tempfile
import zipfile
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name, default)
    return v.strip() if isinstance(v, str) else v


def install_chromedriver() -> str:
    driver_path = get_env("CHROMEDRIVER_PATH")
    if driver_path:
        return driver_path

    for candidate in ("/usr/bin/chromedriver", "/usr/local/bin/chromedriver"):
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
        return ChromeDriverManager().install()
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def create_auth_extension(host: str, port: str, username: str, password: str) -> str:
    manifest_json = """
    {"version":"1.0.0","manifest_version":2,"name":"Chrome Proxy","permissions":["proxy","tabs","unlimitedStorage","storage","<all_urls>","webRequest","webRequestBlocking"],"background":{"scripts":["background.js"]}}
    """
    background_js = string.Template(
        """
        var config = {mode: "fixed_servers", rules: {singleProxy: {scheme: "http", host: "${host}", port: parseInt(${port})}, bypassList: ["<local>"]}};
        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
        function callbackFn(details) { return { authCredentials: { username: "${username}", password: "${password}" } }; }
        chrome.webRequest.onAuthRequired.addListener(callbackFn, {urls: ["<all_urls>"]}, ["blocking"]);
        """
    ).substitute(host=host, port=port, username=username, password=password)

    tmpdir = tempfile.mkdtemp(prefix="chrome-proxy-")
    plugin_path = os.path.join(tmpdir, "proxyauth_plugin.zip")
    with zipfile.ZipFile(plugin_path, "w") as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)
    return plugin_path


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

    options = Options()
    chrome_binary = get_env("CHROME_BIN")
    if chrome_binary and os.path.exists(chrome_binary):
        options.binary_location = chrome_binary
    options.add_argument("--proxy-server=http://%s:%s" % (host, port))
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    if not shim_enabled and user and pwd:
        options.add_extension(create_auth_extension(host, port, user, pwd))

    service = Service(executable_path=install_chromedriver())
    driver = webdriver.Chrome(service=service, options=options)
    try:
        # 使用 HTTP 避免证书问题
        driver.get(get_env("TARGET_URL", "http://httpbin.org/ip"))
        print(driver.page_source[:500])
    finally:
        driver.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
