# 亿牛云爬虫代理（隧道代理）使用说明

本仓库对应帮助站的“爬虫代理”。程序连接固定代理域名和端口，使用用户名、密码认证，由平台调度出口 IP。动态转发和固定转发适用场景不同，接入前先确认订单类型。

## 官方帮助

[帮助首页](https://www.16yun.cn/help/) · [首次接入](https://www.16yun.cn/help/quickstart/crawler-extract/) · [开发手册](https://www.16yun.cn/help/dev-manual/crawler-proxy-guide/) · [开发 FAQ](https://www.16yun.cn/help/dev-manual/crawler-proxy-faq/) · [代码示例与 SDK](https://www.16yun.cn/help/code-sdk/crawler-proxy/) · [错误码说明](https://www.16yun.cn/help/dev-manual/errcode/)

## 首次接入

1. 登录亿牛云控制台，开通爬虫代理订单。
2. 在“当前代理”的订单详情中取得域名、端口、用户名和密码。按用户名与密码配置代理认证。
3. 选择语言和请求库，按示例 README 安装依赖并填写接入参数。
4. 先访问 IP 查询地址验证出口，再测试保持 IP 或切换 IP 的业务流程。

详细步骤见[爬虫代理提取](https://www.16yun.cn/help/quickstart/crawler-extract/)。浏览器自动化应先确认使用适合的固定转发产品，参见[产品说明](https://www.16yun.cn/help/product-intro/crawler-proxy-product/)。

## 运行第一个示例

以下命令从独立仓库 `demo-sdk-tunnel-proxy` 根目录执行；如果使用总仓库 `demo-sdk`，先执行 `cd tunnel-proxy`。需要 Python 和 pip，依赖见[requests 示例](python/requests/README.md)。

```bash
cd python/requests
pip install -r requirements.txt
export PROXY_HOST='<订单代理域名>'
export PROXY_PORT='<订单代理端口>'
export PROXY_USERNAME='<订单用户名>'
export PROXY_PASSWORD='<订单密码>'
export TARGET_URL='https://httpbin.org/ip'
# 可选：为支持此变量的示例指定会话标识
export PROXY_TUNNEL='12345'
python main.py
```

该示例会依次演示新建连接、连接复用、HTTP 和 HTTPS 的 `Proxy-Tunnel` 控制。部分场景使用代码中固定的 IP 查询地址。其他库支持的参数、场景和 HTTPS 限制见各自 README。

## 认证与 IP 控制

| 需求 | 接入要点 |
| --- | --- |
| 代理认证 | 优先使用请求库的代理认证配置；需要手动认证时使用 `Proxy-Authorization: Basic <base64>`，编码内容为 `用户名:密码` |
| 触发重新分配出口 | 动态转发场景下新建 TCP 连接；关闭连接池复用，按库设置 `Connection: Close`、`Proxy-Connection: Close` |
| 同一连接保持出口 | 在代理有效期内复用同一 TCP 连接；HTTP Session 对象仍可能创建多条连接 |
| 按请求组保持或切换 | 使用 `Proxy-Tunnel` 标识，在有效期内保持同组出口；更换标识触发重新分配 |
| HTTPS 的 `Proxy-Tunnel` | 自定义头必须在 CONNECT 阶段发送给代理，仅设置目标请求头可能无效 |

重新分配不保证得到从未使用过的 IP；会话保持也受代理有效期影响。支持 `Proxy-Tunnel` 的 HTTP 访问与 HTTPS 访问是两个独立能力，应核对具体示例。头字段名是 `Proxy-Tunnel`；示例使用的环境变量名是 `PROXY_TUNNEL`。

不要用目标站的 `Authorization` 替代代理认证。具体规则见[爬虫代理开发手册](https://www.16yun.cn/help/dev-manual/crawler-proxy-guide/)。

## 语言与示例

| 语言 | 示例 |
| --- | --- |
| [C++](cpp/README.md) | [cpr](cpp/cpr/README.md)、[libcurl](cpp/libcurl/README.md) |
| [C#](csharp/README.md) | [httpclient](csharp/httpclient/README.md)、[httpwebrequest](csharp/httpwebrequest/README.md) |
| [Dart](dart/README.md) | [dio](dart/dio/README.md)（暂无源码）、[http](dart/http/README.md)（暂无源码） |
| [Go](golang/README.md) | [net_http](golang/net_http/README.md)、[resty](golang/resty/README.md) |
| [Java](java/README.md) | [httpclient4](java/httpclient4/README.md)（暂无源码）、[httpurlconnection](java/httpurlconnection/README.md)（暂无源码）、[jsoup](java/jsoup/README.md)（暂无源码）、[okhttp](java/okhttp/README.md)（暂无源码） |
| [Kotlin](kotlin/README.md) | [okhttp](kotlin/okhttp/README.md)（暂无源码） |
| [Node.js](nodejs/README.md) | [axios](nodejs/axios/README.md)、[casperjs](nodejs/casperjs/README.md)、[got](nodejs/got/README.md)、[http](nodejs/http/README.md)、[https_agent](nodejs/https_agent/README.md)、[https_connect_headers](nodejs/https_connect_headers/README.md)、[https_connect_loop](nodejs/https_connect_loop/README.md)、[phantomjs](nodejs/phantomjs/README.md)、[playwright](nodejs/playwright/README.md)、[puppeteer](nodejs/puppeteer/README.md)、[request](nodejs/request/README.md)、[superagent](nodejs/superagent/README.md)、[undici](nodejs/undici/README.md) |
| [Perl](perl/README.md) | [lwp](perl/lwp/README.md) |
| [PHP](php/README.md) | [curl](php/curl/README.md)、[guzzle](php/guzzle/README.md)、[stream](php/stream/README.md) |
| [Python](python/README.md) | [aiohttp](python/aiohttp/README.md)、[feapder](python/feapder/README.md)、[httpx](python/httpx/README.md)、[mitmproxy](python/mitmproxy/README.md)、[pyppeteer](python/pyppeteer/README.md)、[requests](python/requests/README.md)、[requests_connect_adapter](python/requests_connect_adapter/README.md)、[scrapy](python/scrapy/README.md)、[scrapy_splash](python/scrapy_splash/README.md)、[selenium_chrome](python/selenium_chrome/README.md)、[selenium_firefox](python/selenium_firefox/README.md)、[urllib](python/urllib/README.md) |
| [Ruby](ruby/README.md) | [faraday](ruby/faraday/README.md)、[httparty](ruby/httparty/README.md) |
| [Rust](rust/README.md) | [isahc](rust/isahc/README.md)、[reqwest](rust/reqwest/README.md) |
| [Swift](swift/README.md) | [alamofire](swift/alamofire/README.md)、[urlsession](swift/urlsession/README.md) |

## 常见问题

| 现象或状态码 | 排查动作 |
| --- | --- |
| 407 | 核对域名、端口、用户名、密码，以及库是否发送代理认证 |
| 429 | 降低全部线程和进程的总请求速率，按订单额度控制并发 |
| HTTPS 失败而 HTTP 正常 | 检查代理认证和自定义头是否在 CONNECT 阶段发送 |
| IP 没有按预期切换 | 检查订单类型、连接复用和 `Proxy-Tunnel` 值；重新分配可能重复得到同一 IP |
| 保持 IP 失败 | 检查是否超出代理有效期、连接是否重建、请求是否使用相同标识 |
| 连接不通或出口未变化 | 先用最小代理请求验证网络、认证和请求是否实际经过代理 |

更多说明见[开发 FAQ](https://www.16yun.cn/help/dev-manual/crawler-proxy-faq/)和[错误码说明](https://www.16yun.cn/help/dev-manual/errcode/)。浏览器或本地工具接入可参考[Portunnel 工具导读](https://www.16yun.cn/help/dev-manual/portunnel-tool/)。
