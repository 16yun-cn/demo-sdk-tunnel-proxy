## 16YUN(亿牛云) 爬虫代理隧道使用说明

本说明文档基于以下官方文档整理、合并，并补充了 Python 场景的实践要点与示例代码：
- 接入示例: [https://www.16yun.cn/help/ss_demo/](https://www.16yun.cn/help/ss_demo/)
- 常见问题(爬虫代理): [https://www.16yun.cn/help/s_fq/](https://www.16yun.cn/help/s_fq/)
- 购买/开通与使用引导: [https://www.16yun.cn/help/nu_demo/](https://www.16yun.cn/help/nu_demo/)
- 隧道转发与细节说明: [https://www.16yun.cn/help/ss_detail/](https://www.16yun.cn/help/ss_detail/)

- 正式测试与矩阵说明保留在源仓库 demo-sdk 中；当前发布镜像仓库仅包含对应产品线 demo，不包含 tools/ 与 docs/ 测试体系。

---

### 一、产品概述

- 自营线路、海量 IP 资源池，HTTP/HTTPS 协议可用，7x24 稳定运行。
- 智能检测与负载均衡，云端自动进行 IP 池管理与切换，毫秒级切换无感知。
- 两种 IP 切换模式：
  - 每个请求自动切换 IP（默认）。
  - 用户自主切换/保持 IP（使用 `Proxy-Tunnel` 头、或保持同一 TCP 会话 Keep-Alive）。
- 常见 IP 有效时间：20 秒 / 180 秒可选（以实际产品为准）。

---

### 二、准备与开通

1) 注册并登录后台，选择并开通爬虫代理产品。
2) 在后台「当前代理」中将本机外网 IP 加入 IP 白名单（如需）。
3) 在「代理描述」查看接入信息：域名、端口、用户名、密码等。
   - 隧道域名示例：`t.16yun.cn:31111`（以实际开通信息为准）。

参考文档：[购买/开通与使用引导](https://www.16yun.cn/help/nu_demo/)

---

### 三、环境变量与快速开始

- 环境变量（用于本仓库示例与测试脚本）：
  - `TUNNEL`：形如 `user:pass@host:port` 的接入串；例如：`export TUNNEL="username:password@t.16yun.cn:31111"`。
  - 可选分解变量：`PROXY_HOST`、`PROXY_PORT`、`PROXY_USERNAME`、`PROXY_PASSWORD`。
  - `TARGET_URL`：目标站点调试地址（如 `https://httpbin.org/ip`）。
  - `PROXY-TUNNEL`：若需要固定某个 `Proxy-Tunnel` 值，可通过该变量传入。

- 最小示例（Python requests，HTTP 场景）：
  ```bash
  export TUNNEL="username:password@t.16yun.cn:31111"
  python main.py
  ```


---

### 四、IP 切换与保持策略

- 每请求自动切换 IP（默认）：
  - 适合需要大量不同 IP 的单请求/短会话访问。
  - 对于 HTTPS，协议默认会保持会话（Keep-Alive），同一 HTTPS 会话中 IP 不变；若需“强制每次请求切换 IP”，可在请求头中设置 `Connection: Close` 与 `Proxy-Connection: Close`。

- 保持 IP 不变（同一会话）：
  - 保证该组请求在一个 TCP(Keep-Alive) 会话中，且在代理有效期内完成。
  - 对需要登录 + 获取数据等“多个请求同一 IP”的场景非常有用。

- 使用 `Proxy-Tunnel` 头进行“用户自定义切换/保持”：
  - 设置 `Proxy-Tunnel: <随机数>`。随机数相同的一组请求会在代理有效期内使用同一出口 IP；不同随机数则使用不同 IP。
  - 访问 HTTPS 目标时，由于 CONNECT 隧道，请务必确认库在发起 CONNECT 时就带上该头（部分高封装库需特别留意）。

参考文档：[接入示例](https://www.16yun.cn/help/ss_demo/)、[隧道细节](https://www.16yun.cn/help/ss_detail/)

---

### 五、认证方式

- 用户名/密码认证：
  - 建议使用代理库自带的“代理认证”能力；或设置 `Proxy-Authorization: Basic <base64>`（`<base64>` 为 `用户名:密码` 的 Base64）。
  - 若错误，可能返回 `401 Unauthorized` 或 `407 Proxy Authentication Required`。
- 注意：访问 HTTPS 目标时，尽量不要手动设置通用的 `Authorization` 头，避免被转发到目标站导致匿名失效。优先使用库自带的代理认证接口。

参考文档：[接入示例-用户密码认证](https://www.16yun.cn/help/ss_demo/)
