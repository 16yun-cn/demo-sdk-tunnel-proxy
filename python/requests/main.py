#!/usr/bin/env python3
"""
16YUN(亿牛云) Python requests 隧道代理演示

本示例演示四种隧道代理使用场景：
- 场景A：每次新建连接（强制IP切换）
- 场景B：Keep-Alive会话保持（相同IP）
- 场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标）
- 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标）✅支持

技术特点：
- requests支持通过HTTPAdapter.proxy_headers()在CONNECT阶段添加Proxy-Tunnel头
- 完整的四种场景实现，覆盖所有代理使用模式
- 详细的中文注释和技术原理说明
"""

from __future__ import annotations

import json
import logging
import os
import random
import sys
from typing import Dict, Optional

import requests
import requests.adapters
from requests.auth import HTTPProxyAuth


def setup_logging() -> None:
    """设置日志格式"""
    logging.basicConfig(
        level=logging.INFO, 
        format="%(asctime)s %(levelname)s %(message)s"
    )


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    """获取环境变量，支持别名映射"""
    value = os.getenv(name, default)
    if value is not None and isinstance(value, str):
        value = value.strip()
    return value


def build_proxy_url(host: str, port: str) -> str:
    """构建代理URL"""
    user = get_env("PROXY_USERNAME", "user") or get_env("PROXY_USER", "user")
    pwd = get_env("PROXY_PASSWORD") or get_env("PROXY_PASS", "password")
    
    if user and pwd:
        return f"http://{user}:{pwd}@{host}:{port}"
    return f"http://{host}:{port}"


def build_proxies(host: str, port: str) -> Dict[str, str]:
    """构建代理配置字典"""
    url = build_proxy_url(host, port)
    return {"http": url, "https": url}


def build_auth() -> Optional[HTTPProxyAuth]:
    """构建代理认证，支持别名
    
    注：由于我们将认证信息包含了代理URL中，这就足够了。
    保留此函数但不返回对象，以免重复添加或造成冲突。
    """
    return None


def extract_ip(response_text: str) -> str:
    """从httpbin响应中提取IP地址"""
    try:
        data = json.loads(response_text)
        return data.get("origin", "未知IP")
    except (json.JSONDecodeError, AttributeError):
        return "解析失败"


def scenario_a_force_new_connection() -> None:
    """场景A：每次新建连接（强制IP切换）
    
    技术原理：每次请求不复用Session，添加Connection: close头，强制断开连接
    适用场合：需要每个请求都使用不同IP的场景
    """
    print("\n=== 场景A：每次新建连接（强制IP切换） ===")
    print("技术原理：每次请求不复用Session，添加Connection: close头，强制断开连接")
    print("适用场合：需要每个请求都使用不同IP的场景")
    
    host = get_env("PROXY_HOST", "t.16yun.cn")
    port = get_env("PROXY_PORT", "31111")
    proxies = build_proxies(host, port)
    auth = build_auth()
    target_url = get_env("TARGET_URL", "https://httpbin.org/ip")
    
    # 强制关闭连接的头
    headers = {
        "Connection": "close",
        "Proxy-Connection": "close",
    }
    
    for i in range(1, 3):
        # 每次创建新的请求，不复用连接
        response = requests.get(
            target_url, 
            proxies=proxies, 
            auth=auth, 
            headers=headers,
            timeout=15,
        )
        
        if response.status_code == 200:
            ip = extract_ip(response.text)
            print(f"请求 {i} - IP: {ip}")
        else:
            print(f"请求 {i} 失败 - 状态码: {response.status_code}")


def scenario_b_keep_alive() -> None:
    """场景B：Keep-Alive会话保持（相同IP）
    
    技术原理：复用同一个Session实例，保持TCP连接，在代理有效期内使用相同IP
    适用场合：需要多个请求保持相同IP的场景，如登录流程
    """
    print("\n=== 场景B：Keep-Alive会话保持（相同IP） ===")
    print("技术原理：复用同一个Session实例，保持TCP连接，在代理有效期内使用相同IP")
    print("适用场合：需要多个请求保持相同IP的场景，如登录流程")
    
    host = get_env("PROXY_HOST", "t.16yun.cn")
    port = get_env("PROXY_PORT", "31111")
    proxies = build_proxies(host, port)
    auth = build_auth()
    target_url = get_env("TARGET_URL", "https://httpbin.org/ip")
    
    # 创建会话并保持连接
    session = requests.Session()
    headers = {
        "Connection": "keep-alive",
        "Proxy-Connection": "keep-alive",
    }
    
    for i in range(1, 3):
        response = session.get(
            target_url,
            proxies=proxies,
            auth=auth,
            headers=headers,
            timeout=15,
        )
        
        if response.status_code == 200:
            ip = extract_ip(response.text)
            print(f"请求 {i} - IP: {ip}")
        else:
            print(f"请求 {i} 失败 - 状态码: {response.status_code}")
    
    session.close()


def scenario_c_proxy_tunnel_http() -> None:
    """场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标）
    
    技术原理：在HTTP请求头中添加Proxy-Tunnel，相同值保持相同IP
    适用场合：需要自定义控制IP切换的HTTP访问场景
    """
    print("\n=== 场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标） ===")
    print("技术原理：在HTTP请求头中添加Proxy-Tunnel，相同值保持相同IP")
    print("适用场合：需要自定义控制IP切换的HTTP访问场景")
    
    host = get_env("PROXY_HOST", "t.16yun.cn")
    port = get_env("PROXY_PORT", "31111")
    proxies = build_proxies(host, port)
    auth = build_auth()
    tunnel_value = get_env("PROXY_TUNNEL", "")
    
    # 如果没有设置PROXY_TUNNEL，生成一个随机值
    if not tunnel_value:
        tunnel_value = str(random.randint(1, 10000))
    
    print(f"使用Proxy-Tunnel值: {tunnel_value}")
    
    session = requests.Session()
    headers = {
        "Proxy-Tunnel": tunnel_value,
        "Connection": "keep-alive",
    }
    
    for i in range(1, 3):
        response = session.get(
            "http://httpbin.org/ip",  # HTTP目标
            proxies=proxies,
            auth=auth,
            headers=headers,
            timeout=15,
        )
        
        if response.status_code == 200:
            ip = extract_ip(response.text)
            print(f"请求 {i} - IP: {ip}")
        else:
            print(f"请求 {i} 失败 - 状态码: {response.status_code}")
    
    session.close()


class HTTPSProxyTunnelAdapter(requests.adapters.HTTPAdapter):
    """自定义HTTPAdapter，支持在CONNECT阶段添加Proxy-Tunnel头
    
    这是requests支持HTTPS Proxy-Tunnel的关键实现
    """
    
    def __init__(self, tunnel_value: Optional[str] = None, *args, **kwargs):
        self.tunnel_value = tunnel_value
        super().__init__(*args, **kwargs)
    
    def proxy_headers(self, proxy):
        """重写proxy_headers方法，在CONNECT阶段添加Proxy-Tunnel头"""
        headers = super().proxy_headers(proxy)
        if self.tunnel_value:
            headers['Proxy-Tunnel'] = self.tunnel_value
        return headers


def scenario_c_proxy_tunnel_https() -> None:
    """场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标）✅
    
    技术原理：requests通过自定义HTTPAdapter.proxy_headers()在CONNECT阶段携带Proxy-Tunnel头
    适用场合：需要自定义控制IP切换的HTTPS访问场景
    """
    print("\n=== 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标） ===")
    print("技术原理：requests通过自定义HTTPAdapter.proxy_headers()在CONNECT阶段携带Proxy-Tunnel头")
    print("适用场合：需要自定义控制IP切换的HTTPS访问场景")
    
    host = get_env("PROXY_HOST", "t.16yun.cn")
    port = get_env("PROXY_PORT", "31111")
    proxies = build_proxies(host, port)
    auth = build_auth()
    tunnel_value = get_env("PROXY_TUNNEL", "")
    
    # 如果没有设置PROXY_TUNNEL，生成一个随机值
    if not tunnel_value:
        tunnel_value = str(random.randint(1, 10000))
    
    print(f"使用Proxy-Tunnel值: {tunnel_value}")
    
    # 创建带有Proxy-Tunnel支持的Session
    session = requests.Session()
    adapter = HTTPSProxyTunnelAdapter(tunnel_value=tunnel_value)
    session.mount('https://', adapter)
    
    for i in range(1, 3):
        response = session.get(
            "https://httpbin.org/ip",  # HTTPS目标
            proxies=proxies,
            auth=auth,
            timeout=15,
        )
        
        if response.status_code == 200:
            ip = extract_ip(response.text)
            print(f"请求 {i} - IP: {ip}")
        else:
            print(f"请求 {i} 失败 - 状态码: {response.status_code}")
    
    session.close()


def main() -> int:
    """主函数：演示四种场景"""
    print("16YUN(亿牛云) Python requests 隧道代理演示")
    print("支持的环境变量：")
    print("  PROXY_HOST (默认: t.16yun.cn)")
    print("  PROXY_PORT (默认: 31111)")
    print("  PROXY_USERNAME / PROXY_USER (默认: user)")
    print("  PROXY_PASSWORD / PROXY_PASS (默认: password)")
    print("  PROXY_TUNNEL (可选: 自定义tunnel值)")
    print("  TARGET_URL (默认: https://httpbin.org/ip)")
    
    setup_logging()
    
    host = get_env("PROXY_HOST", "t.16yun.cn")
    port = get_env("PROXY_PORT", "31111")
    
    if not host or not port:
        logging.error("请设置 PROXY_HOST/PROXY_PORT；示例：t.16yun.cn / 31111")
        return 2
    
    # 执行四种场景演示
    try:
        scenario_a_force_new_connection()
        scenario_b_keep_alive()
        scenario_c_proxy_tunnel_http()
        scenario_c_proxy_tunnel_https()
        
        print("\n演示完成！")
        print("注意：requests通过自定义HTTPAdapter支持HTTPS下的Proxy-Tunnel")
        return 0
        
    except Exception as e:
        logging.error(f"演示过程中发生错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
