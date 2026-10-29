# Python scrapy_splash 隧道代理示例

演示使用 scrapy_splash 通过代理访问 HTTP/HTTPS 站点。

## 功能特性
- 场景A：强制IP切换 - 每次请求不同IP
- 场景B：会话保持 - 复用连接保持IP
- 场景C：Proxy-Tunnel固定IP
  - HTTP: ✅ 支持
  - HTTPS: ✅ 支持

## 环境要求
- Python 环境
- 依赖库: scrapy_splash (见代码目录)

## 环境变量配置
| 变量名 | 默认值 | 说明 |
|---|---|---|
| PROXY_HOST | 127.0.0.1 | 订单代理地址 |
| PROXY_PORT | 31111 | 代理端口 |
| PROXY_USERNAME | user | 订单用户名；兼容 PROXY_USER |
| PROXY_PASSWORD | password | 订单密码；兼容 PROXY_PASS |
| TARGET_URL | http://httpbin.org/ip | 目标 URL |

请将代理地址、端口、用户名和密码显式设置为订单信息；表中默认值只说明当前代码行为。当前启动入口默认连接本机代理，接入线上订单时需要覆盖 `PROXY_HOST`。

## 运行方式

以下命令从对应独立仓库根目录执行；使用总仓库 `demo-sdk` 时，先执行 `cd tunnel-proxy`。

```bash
# 1. 进入目录
cd python/scrapy_splash

# 2. 安装依赖 (视语言而定)
pip install -r requirements.txt

# 3. 运行代码
python main.py
```
