import scrapy


class HttpbinSpider(scrapy.Spider):
    name = "httpbin"

    def start_requests(self):  # type: ignore[override]
        yield scrapy.Request("https://httpbin.org/ip", callback=self.parse)

    def parse(self, response):  # type: ignore[override]
        self.logger.info("status=%s body=%s", response.status, response.text[:200])


