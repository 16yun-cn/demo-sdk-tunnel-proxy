# Python scrapy_splash 隧道代理示例

先按[产品接入说明](../../README.md)取得订单信息。运行步骤从对应独立仓库根目录执行；使用总仓库时先进入 `tunnel-proxy`。使用订单的域名、端口、用户名和密码；下表中的默认值仅用于示例，请替换为订单信息。

演示使用 scrapy_splash 通过代理访问 HTTP/HTTPS 站点。

## 使用前提

需要可访问的 Splash 服务；当前配置的地址是 `http://127.0.0.1:8050`（见 `tutorial/settings.py`）。此项目通过 `SplashRequest` 访问目标，不能据此确认已在 Splash 到目标站的链路上完成代理认证或 HTTPS 的 `Proxy-Tunnel` 控制，需在自己的 Splash 环境中核对。

## 示例内容

入口为 `httpbin` spider，使用 `SplashRequest` 和订单代理参数请求 IP 查询地址；可用 `TUNNEL_SEED` 设置请求中的标识。此目录未提供独立的四场景演示。

## 环境要求

- Python 环境
- 依赖库: scrapy_splash (见代码目录)

## 环境变量配置

| 变量名 | 默认值 | 说明 |
|---|---|---|
| PROXY_HOST | t.16yun.cn | 代理地址 |
| PROXY_PORT | 31111 | 代理端口 |
| PROXY_USERNAME | 以代码为准 | 订单用户名 |
| PROXY_PASSWORD | 以代码为准 | 订单密码 |
| TUNNEL_SEED | 未设置 | 请求标识；目标地址固定在 spider 中 |

## 运行方式

```bash
# 1. 进入目录
cd python/scrapy_splash

# 2. 安装依赖 (视语言而定)
pip install -r requirements.txt

# 3. 运行代码
scrapy crawl httpbin
```

## 官方帮助

[帮助首页](https://www.16yun.cn/help/) · [首次接入](https://www.16yun.cn/help/quickstart/crawler-extract/) · [开发手册](https://www.16yun.cn/help/dev-manual/crawler-proxy-guide/) · [开发 FAQ](https://www.16yun.cn/help/dev-manual/crawler-proxy-faq/) · [代码示例与 SDK](https://www.16yun.cn/help/code-sdk/crawler-proxy/) · [错误码说明](https://www.16yun.cn/help/dev-manual/errcode/)
