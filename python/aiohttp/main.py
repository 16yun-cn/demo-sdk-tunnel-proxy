#!/usr/bin/env python3
"""
Python aiohttp 隧道代理四种场景演示
基于16YUN爬虫代理服务的完整实现

四种场景说明：
A. 强制新建连接 - 每次请求建立新连接，获得不同IP
B. Keep-Alive会话保持 - 复用TCP连接，保持相同IP  
C. Proxy-Tunnel固定IP (HTTP) - 使用Proxy-Tunnel头固定IP访问HTTP目标
C. Proxy-Tunnel固定IP (HTTPS) - 使用Proxy-Tunnel头固定IP访问HTTPS目标

注意：Python aiohttp支持在HTTPS场景下使用Proxy-Tunnel头，
通过proxy_headers参数可以在CONNECT阶段添加自定义头
"""

import asyncio
import json
import os
import re
import sys
from typing import Optional

import aiohttp

# 代理配置信息
PROXY_HOST = os.getenv("PROXY_HOST", "t.16yun.cn")
PROXY_PORT = os.getenv("PROXY_PORT", "31111")
PROXY_USER = os.getenv("PROXY_USERNAME") or os.getenv("PROXY_USER", "user")
PROXY_PASS = os.getenv("PROXY_PASSWORD") or os.getenv("PROXY_PASS", "password")
PROXY_TUNNEL = os.getenv("PROXY_TUNNEL", "python-aiohttp-demo-12345")

# 目标URL配置
HTTP_TARGET_URL = "http://httpbin.org/ip"
HTTPS_TARGET_URL = os.getenv("TARGET_URL", "https://httpbin.org/ip")


async def main():
    """主函数：演示四种场景"""
    print("=== Python aiohttp 隧道代理四种场景演示 ===")
    print(f"代理服务器: {PROXY_HOST}:{PROXY_PORT}")
    print(f"代理用户: {PROXY_USER}")
    print(f"Proxy-Tunnel: {PROXY_TUNNEL}")
    print()

    try:
        # 场景A：强制新建连接（每次不同IP）
        print("【场景A】强制新建连接 - 每次请求建立新连接获得不同IP")
        await scenario_a_force_new_connection()
        print()

        # 场景B：Keep-Alive会话保持（相同IP）
        print("【场景B】Keep-Alive会话保持 - 复用TCP连接保持相同IP")
        await scenario_b_keep_alive()
        print()

        # 场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标）
        print("【场景C-HTTP】Proxy-Tunnel固定IP - HTTP目标")
        await scenario_c_proxy_tunnel_http()
        print()

        # 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标，支持）
        print("【场景C-HTTPS】Proxy-Tunnel固定IP - HTTPS目标（支持proxy_headers）")
        await scenario_c_proxy_tunnel_https()
        print()

        print("=== 所有场景演示完成 ===")

    except Exception as e:
        print(f"执行错误: {e}", file=sys.stderr)
        sys.exit(1)


async def scenario_a_force_new_connection():
    """
    场景A：强制新建连接
    每次请求建立新的TCP连接，关闭连接复用
    这样可以获得不同的出口IP地址
    """
    print("技术原理：每次创建新ClientSession，禁用连接复用，添加Connection: close头")
    
    proxy = f"http://{PROXY_HOST}:{PROXY_PORT}"
    proxy_auth = aiohttp.BasicAuth(PROXY_USER, PROXY_PASS)
    
    for i in range(3):
        # 每次创建新的ClientSession，避免连接复用
        connector = aiohttp.TCPConnector(
            limit=1,  # 限制连接数
            limit_per_host=1,  # 每个主机限制连接数
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(
                HTTPS_TARGET_URL,
                proxy=proxy,
                proxy_auth=proxy_auth,
                headers={
                    "Connection": "close",
                    "Proxy-Connection": "close"
                },
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                content = await response.text()
                ip = extract_ip(content)
                
                print(f"请求 {i + 1}: {response.status} - {ip}")
                
                # 短暂延迟确保连接完全关闭
                await asyncio.sleep(0.5)


async def scenario_b_keep_alive():
    """
    场景B：Keep-Alive会话保持
    复用同一个ClientSession实例，保持TCP连接
    在代理会话有效期内保持相同的出口IP
    """
    print("技术原理：复用同一ClientSession实例，保持TCP连接和Keep-Alive")
    
    proxy = f"http://{PROXY_HOST}:{PROXY_PORT}"
    proxy_auth = aiohttp.BasicAuth(PROXY_USER, PROXY_PASS)
    
    # 复用同一个ClientSession实例
    connector = aiohttp.TCPConnector(
        limit=10,  # 允许更多连接
        limit_per_host=5,  # 每个主机允许更多连接
        keepalive_timeout=30,
        enable_cleanup_closed=True,
    )
    
    async with aiohttp.ClientSession(connector=connector) as session:
        for i in range(3):
            async with session.get(
                HTTPS_TARGET_URL,
                proxy=proxy,
                proxy_auth=proxy_auth,
                headers={
                    "Connection": "keep-alive",
                    "Proxy-Connection": "keep-alive"
                },
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                content = await response.text()
                ip = extract_ip(content)
                
                print(f"请求 {i + 1}: {response.status} - {ip}")
                
                # 短暂延迟但保持连接
                await asyncio.sleep(0.2)


async def scenario_c_proxy_tunnel_http():
    """
    场景C：Proxy-Tunnel固定IP（HTTP目标）
    使用Proxy-Tunnel头标识固定会话
    相同Proxy-Tunnel值在有效期内使用相同出口IP
    """
    print("技术原理：在HTTP请求头中添加Proxy-Tunnel标识")
    print(f"Proxy-Tunnel值: {PROXY_TUNNEL}")
    
    proxy = f"http://{PROXY_HOST}:{PROXY_PORT}"
    proxy_auth = aiohttp.BasicAuth(PROXY_USER, PROXY_PASS)
    
    
    for i in range(3):
        connector = aiohttp.TCPConnector()
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(
                HTTP_TARGET_URL,
                proxy=proxy,
                proxy_auth=proxy_auth,
                headers={
                    "Proxy-Tunnel": PROXY_TUNNEL,  # 关键：添加Proxy-Tunnel头（仅对HTTP目标有效）
                    "Connection": "keep-alive",
                    "Proxy-Connection": "keep-alive"
                },
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                content = await response.text()
                ip = extract_ip(content)
                
                print(f"请求 {i + 1}: {response.status} - {ip}")
                
                await asyncio.sleep(0.2)


async def scenario_c_proxy_tunnel_https():
    """
    场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标）
    注意：Python aiohttp支持在CONNECT阶段添加自定义头
    通过proxy_headers参数可以实现HTTPS Proxy-Tunnel
    """
    print("技术原理：通过aiohttp的proxy_headers参数在CONNECT阶段添加Proxy-Tunnel")
    print("✅ 优势：Python aiohttp支持CONNECT阶段自定义头，Proxy-Tunnel对HTTPS有效")
    print(f"Proxy-Tunnel值: {PROXY_TUNNEL}")
    
    proxy = f"http://{PROXY_HOST}:{PROXY_PORT}"
    proxy_auth = aiohttp.BasicAuth(PROXY_USER, PROXY_PASS)
    
    
    for i in range(3):
        connector = aiohttp.TCPConnector()
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(
                HTTPS_TARGET_URL,
                proxy=proxy,
                proxy_auth=proxy_auth,
                proxy_headers={"Proxy-Tunnel": PROXY_TUNNEL},  # 关键：这个头会在CONNECT阶段发送
                headers={
                    "Connection": "keep-alive",
                    "Proxy-Connection": "keep-alive"
                },
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                content = await response.text()
                ip = extract_ip(content)
                
                print(f"请求 {i + 1}: {response.status} - {ip} （Proxy-Tunnel生效）")
                
                await asyncio.sleep(0.2)
    
    print("💡 技术优势：aiohttp proxy_headers参数支持HTTPS Proxy-Tunnel")


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
    asyncio.run(main())
