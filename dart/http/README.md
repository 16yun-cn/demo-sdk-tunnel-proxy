# Dart http 隧道代理示例

演示使用 http 通过代理访问 HTTP 站点。

## 功能特性
- 场景A：强制IP切换 - 每次请求不同IP
- 场景B：会话保持 - 复用连接保持IP
- 场景C-HTTP：Proxy-Tunnel固定IP
- HTTPS: ❌ 不支持

## 环境要求
- Dart 环境
- 依赖库: http (见代码目录)

## 环境变量配置
| 变量名 | 默认值 | 说明 |
|---|---|---|
| PROXY_HOST | t.16yun.cn | 代理地址 |
| PROXY_PORT | 31111 | 代理端口 |
| PROXY_USER | user | 用户名 |
| PROXY_PASSWORD | password | 密码 |
| TARGET_URL | http://httpbin.org/ip | 目标URL |

## 运行方式
```bash
# 1. 进入目录
cd tunnel-proxy/dart/http

# 2. 安装依赖 (视语言而定)
# pub get

# 3. 运行代码
dart bin/main.dart
```
