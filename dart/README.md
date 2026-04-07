# Dart 隧道代理演示

本目录包含了Dart语言的隧道代理实现，演示四种不同的代理使用场景。

## 📁 目录结构

- `dio/` - Dart dio库实现（功能丰富的HTTP客户端）
- `http/` - Dart http包实现（官方HTTP库）

## 🎯 四种场景说明

每个实现都包含以下四种场景：

1. **场景A：强制新建连接** - 每次请求获得不同IP
2. **场景B：Keep-Alive会话保持** - 保持相同IP
3. **场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标）** - 固定IP访问HTTP
4. **场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标）** - 固定IP访问HTTPS

## ⚠️ HTTPS Proxy-Tunnel支持

Dart实现对HTTPS Proxy-Tunnel的支持情况：
- **dio**: ⚠️ 需要验证 - 基于HttpClient
- **http**: ⚠️ 需要验证 - 标准库限制

建议：如需确保HTTPS Proxy-Tunnel支持，请使用Go、Python或Node.js。

## 🚀 快速开始

```bash
# dio实现
cd dio
dart pub get
dart run

# http实现
cd http  
dart pub get
dart run
```

## 📚 相关文档

- [16YUN代理服务文档](https://www.16yun.cn/help/tunnel-proxy/)
- [Dart dio文档](https://pub.dev/packages/dio)
- [Dart http文档](https://pub.dev/packages/http)
