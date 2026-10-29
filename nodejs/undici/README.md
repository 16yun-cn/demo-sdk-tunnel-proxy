# Nodejs undici 隧道代理示例

演示使用 undici 通过代理访问 HTTP/HTTPS 站点。

## 功能特性
- 场景A：强制IP切换 - 每次请求不同IP
- 场景B：会话保持 - 复用连接保持IP
- 场景C：Proxy-Tunnel固定IP
  - HTTP: ✅ 支持
  - HTTPS: ✅ 支持

## 环境要求
- Nodejs 环境
- 依赖库: undici (见代码目录)

## 环境变量配置
| 变量名 | 默认值 | 说明 |
|---|---|---|
| PROXY_HOST | t.16yun.cn | 订单代理地址 |
| PROXY_PORT | 31111 | 代理端口 |
| PROXY_USERNAME | username | 订单用户名；兼容 PROXY_USER |
| PROXY_PASSWORD | password | 订单密码；兼容 PROXY_PASS |
| TARGET_URL | https://httpbin.org/ip | 目标 URL |

请将代理地址、端口、用户名和密码显式设置为订单信息；表中默认值只说明当前代码行为。

部分场景在代码中固定使用 HTTP 或 HTTPS 的 IP 查询地址，`TARGET_URL` 不会替换这些固定地址。

## 运行方式

以下命令从对应独立仓库根目录执行；使用总仓库 `demo-sdk` 时，先执行 `cd tunnel-proxy`。

```bash
# 1. 进入目录
cd nodejs/undici

# 2. 安装依赖 (视语言而定)
npm install

# 3. 运行代码
node main.js
```
