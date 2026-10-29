# Dart dio 隧道代理示例

演示使用 dio 通过代理访问 HTTP 站点。本示例不支持 HTTPS 目标，显式配置 HTTPS 会报错退出。

## 功能特性
- 场景A：强制重新分配 - 两次请求分别新建 TCP 连接；出口 IP 可能重复
- 场景B：会话保持 - 两次请求复用连接，在连接及出口有效期内保持 IP
- 场景C：Proxy-Tunnel固定IP - 两次新建连接使用同一标识，在出口有效期内保持 IP
  - HTTP: ✅ 支持
  - HTTPS: ❌ 本示例未实现 CONNECT 阶段的 Proxy-Tunnel 头

## 环境要求
- Dart SDK 3.6.2（构建和验证版本；当前锁定依赖要求 Dart 3.5+）
- 依赖库: Dio, dart:io（见 pubspec.yaml）

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
| TARGET_URL | http://httpbin.org/ip | HTTP 目标 URL |

请将示例用户名和密码替换为实际代理凭据。认证失败或请求失败会非零退出。

## 运行方式
```bash
# 1. 从独立 Tunnel 仓库根目录进入；总仓库先执行 cd tunnel-proxy
cd dart/dio

# 2. 安装依赖
dart pub get

# 3. 配置实际代理凭据并运行
export PROXY_USERNAME="你的代理用户名"
export PROXY_PASSWORD="你的代理密码"
dart bin/main.dart
```
