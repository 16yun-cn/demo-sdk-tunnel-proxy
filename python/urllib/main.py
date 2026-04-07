#!/usr/bin/env python3
"""
Python urllib 隧道代理四种场景演示
基于16YUN爬虫代理服务的完整实现

四种场景说明：
A. 强制新建连接 - 每次请求建立新连接，获得不同IP
B. Keep-Alive会话保持 - 复用TCP连接，保持相同IP  
C. Proxy-Tunnel固定IP (HTTP) - 使用Proxy-Tunnel头固定IP访问HTTP目标
C. Proxy-Tunnel固定IP (HTTPS) - 使用Proxy-Tunnel头固定IP访问HTTPS目标

注意：Python urllib支持在HTTPS场景下使用Proxy-Tunnel头，
通过重载HTTPSConnection.set_tunnel方法可以在CONNECT阶段添加自定义头
"""

import base64
import http.client
import json
import os
import re
import ssl
import sys
import time
import urllib.request
import urllib.parse
from typing import Optional

# 代理配置信息
PROXY_HOST = os.getenv("PROXY_HOST", "t.16yun.cn")
PROXY_PORT = os.getenv("PROXY_PORT", "31111")
PROXY_USER = os.getenv("PROXY_USERNAME") or os.getenv("PROXY_USER", "user")
PROXY_PASS = os.getenv("PROXY_PASSWORD") or os.getenv("PROXY_PASS", "password")
PROXY_TUNNEL = os.getenv("PROXY_TUNNEL", "python-urllib-demo-12345")

# 目标URL配置
HTTP_TARGET_URL = "http://httpbin.org/ip"
HTTPS_TARGET_URL = os.getenv("TARGET_URL", "https://httpbin.org/ip")
def create_ssl_context() -> ssl.SSLContext:
    """Create a verifying SSL context using the system trust store."""
    return ssl.create_default_context()


def main():
    """主函数：演示四种场景"""
    print("=== Python urllib 隧道代理四种场景演示 ===")
    print(f"代理服务器: {PROXY_HOST}:{PROXY_PORT}")
    print(f"代理用户: {PROXY_USER}")
    print(f"Proxy-Tunnel: {PROXY_TUNNEL}")
    print()

    try:
        print("【场景A】强制新建连接 - 每次请求建立新连接获得不同IP")
        scenario_a_force_new_connection()
        print()

        print("【场景B】Keep-Alive会话保持 - 复用TCP连接保持相同IP")
        scenario_b_keep_alive()
        print()

        print("【场景C-HTTP】Proxy-Tunnel固定IP - HTTP目标")
        scenario_c_proxy_tunnel_http()
        print()

        print("【场景C-HTTPS】Proxy-Tunnel固定IP - HTTPS目标（支持自定义CONNECT头）")
        scenario_c_proxy_tunnel_https()
        print()

        print("=== 所有场景演示完成 ===")
        return 0

    except Exception as e:
        print(f"执行错误: {e}", file=sys.stderr)
        return 1


def scenario_a_force_new_connection():
    """
    场景A：强制新建连接
    每次请求建立新的TCP连接，关闭连接复用
    这样可以获得不同的出口IP地址
    """
    print("技术原理：每次创建新opener，添加Connection: close头")
    
    proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
    
    ssl_ctx = create_ssl_context()
    
    for i in range(3):
        # 每次创建新的opener，避免连接复用
        handler = urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
        https_handler = urllib.request.HTTPSHandler(context=ssl_ctx)
        opener = urllib.request.build_opener(handler, https_handler)
        
        req = urllib.request.Request(
            HTTPS_TARGET_URL,
            headers={
                "Connection": "close",
                "Proxy-Connection": "close"
            }
        )
        
        with opener.open(req, timeout=15) as response:
            content = response.read().decode("utf-8", errors="ignore")
            ip = extract_ip(content)
            
            print(f"请求 {i + 1}: {response.status} - {ip}")
            
            # 短暂延迟确保连接完全关闭
            time.sleep(0.5)


def scenario_b_keep_alive():
    """
    场景B：Keep-Alive会话保持
    复用同一个opener实例，保持TCP连接
    在代理会话有效期内保持相同的出口IP
    """
    print("技术原理：复用同一opener实例，保持TCP连接和Keep-Alive")
    
    proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
    
    ssl_ctx = create_ssl_context()
    
    # 复用同一个opener实例
    handler = urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
    https_handler = urllib.request.HTTPSHandler(context=ssl_ctx)
    opener = urllib.request.build_opener(handler, https_handler)
    
    for i in range(3):
        req = urllib.request.Request(
            HTTPS_TARGET_URL,
            headers={
                "Connection": "keep-alive",
                "Proxy-Connection": "keep-alive"
            }
        )
        
        with opener.open(req, timeout=15) as response:
            content = response.read().decode("utf-8", errors="ignore")
            ip = extract_ip(content)
            
            print(f"请求 {i + 1}: {response.status} - {ip}")
            
            # 短暂延迟但保持连接
            time.sleep(0.2)


def scenario_c_proxy_tunnel_http():
    """
    场景C：Proxy-Tunnel固定IP（HTTP目标）
    使用Proxy-Tunnel头标识固定会话
    相同Proxy-Tunnel值在有效期内使用相同出口IP
    """
    print("技术原理：在HTTP请求头中添加Proxy-Tunnel标识")
    print(f"Proxy-Tunnel值: {PROXY_TUNNEL}")
    
    proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
    handler = urllib.request.ProxyHandler({"http": proxy_url})
    opener = urllib.request.build_opener(handler)
    
    for i in range(3):
        req = urllib.request.Request(
            HTTP_TARGET_URL,
            headers={
                "Proxy-Tunnel": PROXY_TUNNEL,  # 关键：添加Proxy-Tunnel头（仅对HTTP目标有效）
                "Connection": "keep-alive",
                "Proxy-Connection": "keep-alive"
            }
        )
        
        with opener.open(req, timeout=15) as response:
            content = response.read().decode("utf-8", errors="ignore")
            ip = extract_ip(content)
            
            print(f"请求 {i + 1}: {response.status} - {ip}")
            
            time.sleep(0.2)


def scenario_c_proxy_tunnel_https():
    """
    场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标）
    注意：Python urllib支持在CONNECT阶段添加自定义头
    通过自定义ProxyHTTPSConnection重载set_tunnel方法实现
    """
    print("技术原理：通过自定义HTTPSConnection重载set_tunnel方法在CONNECT阶段添加Proxy-Tunnel")
    print("✅ 优势：Python urllib支持CONNECT阶段自定义头，Proxy-Tunnel对HTTPS有效")
    print(f"Proxy-Tunnel值: {PROXY_TUNNEL}")
    
    # 使用自定义的ProxyHandler支持HTTPS Proxy-Tunnel
    handler = ProxyTunnelHandler(create_ssl_context())
    opener = urllib.request.build_opener(handler)
    
    for i in range(3):
        req = urllib.request.Request(
            HTTPS_TARGET_URL,
            headers={
                "Connection": "keep-alive",
                "Proxy-Connection": "keep-alive"
            }
        )
        
        with opener.open(req, timeout=15) as response:
            content = response.read().decode("utf-8", errors="ignore")
            ip = extract_ip(content)
            
            print(f"请求 {i + 1}: {response.status} - {ip} （Proxy-Tunnel生效）")
            
            time.sleep(0.2)
    
    print("💡 技术优势：重载HTTPSConnection.set_tunnel支持HTTPS Proxy-Tunnel")


class ProxyTunnelHTTPSConnection(http.client.HTTPSConnection):
    """自定义HTTPS连接类，支持在CONNECT阶段添加Proxy-Tunnel头"""

    def set_tunnel(self, host, port=None, headers=None):
        """重载set_tunnel方法，添加Proxy-Tunnel头"""
        if headers is None:
            headers = {}
        
        # 添加Proxy-Tunnel头到CONNECT请求
        headers["Proxy-Tunnel"] = PROXY_TUNNEL
        
        # 调用父类方法
        super().set_tunnel(host, port, headers)


class ProxyTunnelHandler(urllib.request.HTTPSHandler):
    """自定义HTTPS处理器，使用支持Proxy-Tunnel的连接类"""

    def __init__(self, context: ssl.SSLContext):
        super().__init__(context=context)
        self._context = context

    def https_open(self, req):
        """处理HTTPS请求"""
        return self.do_open(ProxyTunnelHTTPSConnection, req)
    
    def do_open(self, http_class, req):
        """建立连接并发送请求"""
        host = req.host
        if not host:
            raise urllib.request.URLError('no host given')
        
        # 解析代理设置
        proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
        proxy_parts = urllib.parse.urlparse(proxy_url)
        
        # 创建连接
        conn = http_class(proxy_parts.hostname, proxy_parts.port, context=self._context)
        
        # 计算 Proxy-Authorization
        user_pass = f"{proxy_parts.username}:{proxy_parts.password}"
        auth = base64.b64encode(user_pass.encode()).decode()
        headers = {"Proxy-Authorization": f"Basic {auth}"}
        
        # 设置代理隧道（这会调用我们重载的set_tunnel方法）
        conn.set_tunnel(host, 443, headers=headers)
        
        try:
            # 发送请求
            conn.request(req.get_method(), req.selector, req.data, req.headers)
            response = conn.getresponse()
            
            # 包装响应
        # 包装响应
            return urllib.request.addinfourl(response, response.msg, req.get_full_url(), response.status)
        except Exception as e:
            conn.close()
            raise urllib.request.URLError(f"Proxy connection failed: {e}")


def extract_ip(content: str) -> str:
    """从响应内容中提取IP地址"""
    try:
        # 尝试解析JSON响应，适用于httpbin.org/ip
        if '"origin"' in content:
            data = json.loads(content)
            return data.get("origin", "未知IP")
        
        # 使用正则表达式作为备选方案
        match = re.search(r'"origin":\s*"([^"]+)"', content)
        if match:
            return match.group(1)
        
        return "未知IP"
    except Exception:
        return "IP解析失败"


if __name__ == "__main__":
    sys.exit(main())
