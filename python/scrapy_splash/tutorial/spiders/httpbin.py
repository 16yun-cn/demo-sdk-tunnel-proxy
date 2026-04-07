import os
from scrapy_splash import SplashRequest
import scrapy


class HttpBinSpider(scrapy.Spider):
    name = "httpbin"

    def start_requests(self):
        proxy_host = os.getenv("PROXY_HOST", "t.16yun.cn")
        proxy_port = os.getenv("PROXY_PORT", "31111")
        proxy_user = os.getenv("PROXY_USERNAME") or os.getenv("PROXY_USER")
        proxy_pass = os.getenv("PROXY_PASSWORD") or os.getenv("PROXY_PASS")
        seed = os.getenv("TUNNEL_SEED") or os.getenv("PROXY_TUNNEL")
        target_url = os.getenv("TARGET_URL", "http://httpbin.org/ip")

        proxy = f"http://{proxy_host}:{proxy_port}" if not (proxy_user and proxy_pass) else f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
        headers = {"Proxy-Tunnel": seed} if seed else None

        script = '''
            function main(splash)
              local url = splash.args.url
              assert(splash:go(url))
              assert(splash:wait(0.5))
              local entries = splash:history()
              local last_response = entries[#entries].response
              return {
                url = splash:url(),
                http_status = last_response.status,
                html = splash:html(),
                headers = last_response.headers,
              }
            end
        '''
        yield SplashRequest(
            target_url,
            self.parse,
            endpoint="execute",
            args={"lua_source": script, "wait": 1},
            splash_headers=headers,
        )

    def parse(self, response):
        payload = getattr(response, "data", None)
        if payload is None:
            payload = response.json()
        self.logger.info("status=%s", payload.get("http_status"))
        self.logger.info("html=%s", payload.get("html"))
