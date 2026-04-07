BOT_NAME = "tutorial"

SPIDER_MODULES = ["tutorial.spiders"]
NEWSPIDER_MODULE = "tutorial.spiders"

ROBOTSTXT_OBEY = False

DOWNLOADER_MIDDLEWARES = {
    "tutorial.middlewares.ProxyDownloaderMiddleware": 100,
}


