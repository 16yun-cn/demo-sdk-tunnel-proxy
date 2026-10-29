# Kotlin okhttp 隧道代理示例

演示使用 okhttp 通过代理访问 HTTP/HTTPS 站点。

## 功能特性
- 场景A：强制重新分配 - 两次请求分别新建 TCP 连接；出口 IP 可能重复
- 场景B：会话保持 - 两次请求复用连接，在连接及出口有效期内保持 IP
- 场景C：Proxy-Tunnel固定IP - 两次新建连接使用同一标识，在出口有效期内保持 IP
  - HTTP: ✅ 支持
  - HTTPS: ❌ 本示例未实现 CONNECT 阶段的 Proxy-Tunnel 头

场景 A/B 支持普通 HTTP/HTTPS 代理访问。上面的 HTTPS 限制仅指场景 C：目标请求头不能代替 CONNECT 阶段的代理头。

## 环境要求
- JDK 17、Maven 3+（Maven 自动获取 Kotlin 编译器）
- 依赖库: Kotlin Stdlib, OkHttp 4.12.0

## 环境变量配置
| 变量名 | 默认值 | 说明 |
|---|---|---|
| PROXY_HOST | t.16yun.cn | 代理地址 |
| PROXY_PORT | 31111 | 代理端口 |
| PROXY_USERNAME | user | 代理用户名；优先于 `PROXY_USER` |
| PROXY_USER | - | 用户名兼容别名 |
| PROXY_PASSWORD | password | 代理密码；优先于 `PROXY_PASS` |
| PROXY_PASS | - | 密码兼容别名 |
| PROXY_TUNNEL | 自动生成 | 场景 C 共用的请求组标识 |
| TARGET_URL | https://httpbin.org/ip | 场景 A/B 的 HTTP 或 HTTPS 目标 URL |
| TARGET_URL_HTTP | 见下文 | 场景 C 的 HTTP 目标 URL，必须以 `http://` 开头 |

请将示例用户名和密码替换为实际代理凭据。认证失败或请求失败会非零退出。

未设置 `TARGET_URL_HTTP` 时，若 `TARGET_URL` 是 HTTP 则沿用；否则场景 C 使用 `http://httpbin.org/ip`。场景 A/B 仍访问原 `TARGET_URL`。

## 运行方式
```bash
# 1. 从独立 Tunnel 仓库根目录进入；总仓库先执行 cd tunnel-proxy
cd kotlin/okhttp

# 2. 编译并获取依赖
mvn package -q -DskipTests

# 3. 配置实际代理凭据并运行
export PROXY_USERNAME="你的代理用户名"
export PROXY_PASSWORD="你的代理密码"
java -jar target/kotlin-demo-tunnel-0.1.0.jar
```
