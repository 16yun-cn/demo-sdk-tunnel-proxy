# Nodejs phantomjs 隧道代理示例

演示使用 phantomjs 通过代理访问 HTTP/HTTPS 站点。

## 功能特性
- 场景A：强制IP切换 - 每次请求不同IP
- 场景B：会话保持 - 复用连接保持IP
- 场景C：Proxy-Tunnel固定IP
  - HTTP: ✅ 支持
  - HTTPS: ✅ 支持

## 环境要求
- Nodejs 环境
- 依赖库: phantomjs (见代码目录)

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
cd tunnel-proxy/nodejs/phantomjs

# 2. 安装依赖 (视语言而定)
# npm install

# 3. 运行代码
node main.js
```
