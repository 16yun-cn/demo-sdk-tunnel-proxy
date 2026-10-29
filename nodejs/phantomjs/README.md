# Nodejs phantomjs 隧道代理示例

先按[产品接入说明](../../README.md)取得订单信息。运行步骤从对应独立仓库根目录执行；使用总仓库时先进入 `tunnel-proxy`。使用订单的域名、端口、用户名和密码。

演示使用 phantomjs 通过代理访问 HTTP 站点。

## 运行方式

这是 PhantomJS 历史 HTTP 示例，需要预先安装 PhantomJS。脚本访问 `http://httpbin.org/ip`；`Proxy-Tunnel` 头示例处于注释状态。脚本不读取代理环境变量，也未提供完整的四场景或 HTTPS 演示。

从独立仓库根目录执行，将参数替换为订单信息：

```bash
cd nodejs/phantomjs
phantomjs --proxy='<代理域名>:<代理端口>' --proxy-auth='<用户名>:<密码>' http-demo.js
```

需要现代浏览器接入时，可查看 [Playwright 示例](../playwright/README.md)。

## 官方帮助

[帮助首页](https://www.16yun.cn/help/) · [首次接入](https://www.16yun.cn/help/quickstart/crawler-extract/) · [开发手册](https://www.16yun.cn/help/dev-manual/crawler-proxy-guide/) · [开发 FAQ](https://www.16yun.cn/help/dev-manual/crawler-proxy-faq/) · [代码示例与 SDK](https://www.16yun.cn/help/code-sdk/crawler-proxy/) · [错误码说明](https://www.16yun.cn/help/dev-manual/errcode/)
