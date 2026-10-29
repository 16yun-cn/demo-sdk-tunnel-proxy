# Python mitmproxy 隧道代理示例

先按[产品接入说明](../../README.md)取得订单信息。运行步骤从对应独立仓库根目录执行；使用总仓库时先进入 `tunnel-proxy`。使用订单的域名、端口、用户名和密码。

演示使用 mitmproxy 通过代理访问 HTTP/HTTPS 站点。

## 运行方式

本目录是 mitmproxy 插件，入口为 `addon.py`。插件向普通请求注入 `Proxy-Tunnel`，使用 `TUNNEL_SEED` 指定标识（默认 `1`）；它不负责根据代理环境变量配置上游连接，也未实现完整的四场景演示。

先安装 mitmproxy，再从独立仓库根目录执行，将上游代理信息替换为订单信息：

```bash
cd python/mitmproxy
export TUNNEL_SEED='1'
mitmproxy --mode 'upstream:http://<代理域名>:<代理端口>' \
  --set 'upstream_auth=<用户名>:<密码>' -s addon.py
```

将需要调试的客户端连接至本地 mitmproxy。HTTPS 的客户端证书信任和 CONNECT 头支持需按工具配置核对，不能仅凭普通请求头注入认定已支持 HTTPS 的出口控制。上游认证参数见 [mitmproxy 官方选项说明](https://docs.mitmproxy.org/stable/concepts/options/#upstream_auth)。

## 官方帮助

[帮助首页](https://www.16yun.cn/help/) · [首次接入](https://www.16yun.cn/help/quickstart/crawler-extract/) · [开发手册](https://www.16yun.cn/help/dev-manual/crawler-proxy-guide/) · [开发 FAQ](https://www.16yun.cn/help/dev-manual/crawler-proxy-faq/) · [代码示例与 SDK](https://www.16yun.cn/help/code-sdk/crawler-proxy/) · [错误码说明](https://www.16yun.cn/help/dev-manual/errcode/)
