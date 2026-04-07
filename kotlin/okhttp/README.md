# Kotlin okhttp 隧道代理示例

演示使用 okhttp 通过代理访问 HTTP/HTTPS 站点。

## 功能特性
- 场景A：强制IP切换 - 每次请求不同IP
- 场景B：会话保持 - 复用连接保持IP
- 场景C：Proxy-Tunnel固定IP
  - HTTP: ✅ 支持
  - HTTPS: ❌ 不支持

## 环境要求
- Kotlin 环境
- 依赖库: okhttp (见代码目录)

## 环境变量配置
| 变量名 | 默认值 | 说明 |
|---|---|---|
| PROXY_HOST | t.16yun.cn | 代理地址 |
| PROXY_PORT | 31111 | 代理端口 |
| PROXY_USER | user | 用户名 |
| PROXY_PASSWORD | password | 密码 |
| TARGET_URL | https://httpbin.org/ip | 目标URL |

## 运行方式
```bash
# 1. 进入目录
cd tunnel-proxy/kotlin/okhttp

# 2. 安装依赖 (视语言而定)
# mvn install

# 3. 运行代码
mvn package && java -jar target/*.jar
```
