# Swift 隧道代理演示

本目录包含了Swift语言的隧道代理实现，演示四种不同的代理使用场景。

## 📁 目录结构

- `urlsession/` - Swift URLSession实现（系统原生）
- `alamofire/` - Swift Alamofire实现（第三方库）

## 🎯 四种场景说明

每个实现都包含以下四种场景：

1. **场景A：强制新建连接** - 每次请求获得不同IP
2. **场景B：Keep-Alive会话保持** - 保持相同IP
3. **场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标）** - 固定IP访问HTTP
4. **场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标）** - 固定IP访问HTTPS

## ⚠️ HTTPS Proxy-Tunnel支持

Swift实现对HTTPS Proxy-Tunnel的支持情况：
- **URLSession**: ⚠️ 需要验证 - 系统级网络栈限制
- **Alamofire**: ⚠️ 需要验证 - 基于URLSession

建议：如需确保HTTPS Proxy-Tunnel支持，请使用Go、Python或Node.js。

## 🚀 快速开始

```bash
# URLSession实现
cd urlsession
swift run

# Alamofire实现  
cd alamofire
swift run
```

## 📚 相关文档

- [16YUN代理服务文档](https://www.16yun.cn/help/tunnel-proxy/)
- [Apple URLSession文档](https://developer.apple.com/documentation/foundation/urlsession)
- [Alamofire官方文档](https://github.com/Alamofire/Alamofire)
