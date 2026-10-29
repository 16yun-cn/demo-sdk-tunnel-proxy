# Perl 隧道代理演示

本目录包含了Perl语言的隧道代理实现，演示四种不同的代理使用场景。

## 📁 目录结构

- [lwp](lwp/README.md) - Perl LWP::UserAgent实现（标准HTTP库）

## 🎯 四种场景说明

每个实现都包含以下四种场景：

1. **场景A：强制新建连接** - 每次请求获得不同IP
2. **场景B：Keep-Alive会话保持** - 保持相同IP
3. **场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标）** - 固定IP访问HTTP
4. **场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标）** - 固定IP访问HTTPS

## ⚠️ HTTPS Proxy-Tunnel支持

Perl实现对HTTPS Proxy-Tunnel的支持情况：
- **LWP::UserAgent**: ⚠️ 需要验证 - 标准库限制

建议：如需确保HTTPS Proxy-Tunnel支持，请使用Go、Python或Node.js。

## 🚀 快速开始

```bash
# 安装依赖
cpan install LWP::UserAgent JSON

# 运行演示
cd lwp
perl main.pl
```

## 📚 相关文档

- [16YUN 爬虫代理开发手册](https://www.16yun.cn/help/dev-manual/crawler-proxy-guide/)
- [LWP::UserAgent文档](https://metacpan.org/pod/LWP::UserAgent)
- [Perl网络编程指南](https://perldoc.perl.org/perlnetworking)
