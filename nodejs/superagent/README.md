# Nodejs superagent 隧道代理示例

先按[产品接入说明](../../README.md)取得订单信息。运行步骤从对应独立仓库根目录执行；使用总仓库时先进入 `tunnel-proxy`。使用订单的域名、端口、用户名和密码；下表中的默认值仅用于示例，请替换为订单信息。

演示使用 superagent 通过代理访问 HTTP/HTTPS 站点。

## 功能特性

- 场景A：新建连接，触发出口 IP 重新分配
- 场景B：在代理有效期内复用同一连接保持 IP
- 场景C：Proxy-Tunnel 在有效期内控制出口 IP
  - HTTP: ✅ 支持
  - HTTPS: ✅ 支持

## 环境要求

- Nodejs 环境
- 依赖库: superagent (见代码目录)

## 环境变量配置

| 变量名 | 默认值 | 说明 |
|---|---|---|
| PROXY_HOST | t.16yun.cn | 代理地址 |
| PROXY_PORT | 31111 | 代理端口 |
| PROXY_USERNAME | 以代码为准 | 订单用户名 |
| PROXY_PASSWORD | 以代码为准 | 订单密码 |
| TARGET_URL | https://httpbin.org/ip | 目标URL |

## 运行方式

```bash
# 1. 进入目录
cd nodejs/superagent

# 2. 安装依赖 (视语言而定)
npm install

# 3. 运行代码
node main.js
```

## 官方帮助

[帮助首页](https://www.16yun.cn/help/) · [首次接入](https://www.16yun.cn/help/quickstart/crawler-extract/) · [开发手册](https://www.16yun.cn/help/dev-manual/crawler-proxy-guide/) · [开发 FAQ](https://www.16yun.cn/help/dev-manual/crawler-proxy-faq/) · [代码示例与 SDK](https://www.16yun.cn/help/code-sdk/crawler-proxy/) · [错误码说明](https://www.16yun.cn/help/dev-manual/errcode/)
