#!/usr/bin/env python3
"""
16YUN 隧道代理：requests 自定义HTTPAdapter 四种场景演示

四种场景说明：
- 场景A（强制新建连接）：每次请求强制创建新的TCP连接，IP会发生变化
- 场景B（Keep-Alive保持）：复用TCP连接，同一个Session内多次请求保持相同IP
- 场景C-HTTP（HTTP Proxy-Tunnel）：通过Proxy-Tunnel头固定IP（HTTP目标）
- 场景C-HTTPS（HTTPS Proxy-Tunnel）：通过CONNECT阶段Proxy-Tunnel头固定IP（HTTPS目标）
"""
import os
import random
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class TunnelHTTPAdapter(HTTPAdapter):
    """自定义HTTPAdapter，支持在CONNECT阶段注入Proxy-Tunnel头"""
    
    def __init__(self, tunnel_seed: str | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tunnel_seed = tunnel_seed

    def proxy_headers(self, proxy):  # type: ignore[override]
        """重写proxy_headers方法，在CONNECT阶段注入Proxy-Tunnel头"""
        headers = super().proxy_headers(proxy)
        if self.tunnel_seed:
            headers['Proxy-Tunnel'] = self.tunnel_seed
        return headers


def getenv(k: str, default: str | None = None) -> str | None:
    """获取环境变量并去除空白字符"""
    v = os.getenv(k, default)
    return v.strip() if isinstance(v, str) else v


def get_proxy_config():
    """获取代理配置"""
    host = getenv('PROXY_HOST', 't.16yun.cn')
    port = getenv('PROXY_PORT', '31111')
    # 标准环境变量（支持别名兼容）
    user = getenv('PROXY_USERNAME') or getenv('PROXY_USER') or 'username'
    pwd = getenv('PROXY_PASSWORD') or getenv('PROXY_PASS') or 'password'
    tunnel = getenv('PROXY_TUNNEL', '')
    target = getenv('TARGET_URL', 'https://httpbin.org/ip')
    
    proxy_url = f"http://{user}:{pwd}@{host}:{port}"
    proxies = {"http": proxy_url, "https": proxy_url}
    
    return host, port, user, pwd, tunnel, target, proxies


def scenario_a_force_new_connection():
    """
    场景A：强制新建连接
    技术实现：每次请求都创建新的Session，禁用连接复用
    效果：每次请求都会分配不同的出口IP
    适用场合：需要高度随机化IP的爬虫任务
    """
    print("=== 场景A：强制新建连接 ===")
    _, _, _, _, _, target, proxies = get_proxy_config()
    
    for i in range(3):
        # 每次都创建新的Session，强制新建连接
        session = requests.Session()
        # 禁用连接复用
        session.mount('http://', HTTPAdapter(max_retries=0))
        session.mount('https://', HTTPAdapter(max_retries=0))
        
        try:
            response = session.get(target, proxies=proxies, timeout=15)
            ip_info = response.json()
            print(f"  请求 {i+1}: IP = {ip_info.get('origin', 'N/A')}")
        except Exception as e:
            print(f"  请求 {i+1}: 错误 = {e}")
        finally:
            session.close()
    print()


def scenario_b_keep_alive():
    """
    场景B：Keep-Alive会话保持
    技术实现：复用同一个Session对象，启用连接池
    效果：多次请求复用TCP连接，保持相同的出口IP
    适用场合：需要保持会话状态的应用场景
    """
    print("=== 场景B：Keep-Alive会话保持 ===")
    _, _, _, _, _, target, proxies = get_proxy_config()
    
    # 复用同一个Session
    session = requests.Session()
    
    try:
        for i in range(3):
            response = session.get(target, proxies=proxies, timeout=15)
            ip_info = response.json()
            print(f"  请求 {i+1}: IP = {ip_info.get('origin', 'N/A')}")
    except Exception as e:
        print(f"  Keep-Alive请求错误: {e}")
    finally:
        session.close()
    print()


def scenario_c_proxy_tunnel_http():
    """
    场景C-HTTP：HTTP Proxy-Tunnel固定IP
    技术实现：在请求头中添加Proxy-Tunnel
    效果：通过Proxy-Tunnel头固定出口IP（HTTP目标）
    适用场合：HTTP协议下需要固定IP的场景
    注意：HTTP目标可以直接在请求头添加Proxy-Tunnel
    """
    print("=== 场景C-HTTP：HTTP Proxy-Tunnel固定IP ===")
    _, _, _, _, tunnel, _, proxies = get_proxy_config()
    
    # HTTP目标URL
    target_http = "http://httpbin.org/ip"
    tunnel_seed = tunnel or str(random.randint(1, 10000))
    
    session = requests.Session()
    
    try:
        for i in range(3):
            # HTTP请求直接在请求头中添加Proxy-Tunnel
            headers = {'Proxy-Tunnel': tunnel_seed}
            response = session.get(target_http, proxies=proxies, headers=headers, timeout=15)
            ip_info = response.json()
            print(f"  请求 {i+1}: IP = {ip_info.get('origin', 'N/A')} (Proxy-Tunnel: {tunnel_seed})")
    except Exception as e:
        print(f"  HTTP Proxy-Tunnel请求错误: {e}")
    finally:
        session.close()
    print()


def scenario_c_proxy_tunnel_https():
    """
    场景C-HTTPS：HTTPS Proxy-Tunnel固定IP
    技术实现：通过自定义HTTPAdapter在CONNECT阶段注入Proxy-Tunnel头
    效果：通过Proxy-Tunnel头固定出口IP（HTTPS目标）
    适用场合：HTTPS协议下需要固定IP的场景
    注意：HTTPS目标需要在CONNECT阶段携带Proxy-Tunnel头，需要自定义HTTPAdapter
    """
    print("=== 场景C-HTTPS：HTTPS Proxy-Tunnel固定IP ===")
    _, _, _, _, tunnel, target, proxies = get_proxy_config()
    
    tunnel_seed = tunnel or str(random.randint(1, 10000))
    
    session = requests.Session()
    # 为HTTPS请求挂载自定义Adapter（支持CONNECT阶段Proxy-Tunnel）
    session.mount('https://', TunnelHTTPAdapter(tunnel_seed))
    
    try:
        for i in range(3):
            response = session.get(target, proxies=proxies, timeout=15)
            ip_info = response.json()
            print(f"  请求 {i+1}: IP = {ip_info.get('origin', 'N/A')} (Proxy-Tunnel: {tunnel_seed})")
    except Exception as e:
        print(f"  HTTPS Proxy-Tunnel请求错误: {e}")
    finally:
        session.close()
    print()


def main():
    """主函数：演示四种场景的对比效果"""
    print("16YUN 隧道代理 - requests 自定义HTTPAdapter 四种场景演示")
    print("=" * 60)
    
    # 显示当前配置
    host, port, user, tunnel, _, target, _ = get_proxy_config()
    print(f"代理服务器: {host}:{port}")
    print(f"认证用户: {user}")
    print(f"目标URL: {target}")
    print(f"Proxy-Tunnel: {tunnel or '(自动生成)'}")
    print("=" * 60)
    
    # 依次执行四种场景
    scenario_a_force_new_connection()
    scenario_b_keep_alive()
    scenario_c_proxy_tunnel_http()
    scenario_c_proxy_tunnel_https()
    
    print("=" * 60)
    print("场景对比总结：")
    print("- 场景A：每次不同IP（强制新建连接）")
    print("- 场景B：多次相同IP（Keep-Alive复用连接）")
    print("- 场景C-HTTP：固定IP（HTTP Proxy-Tunnel）")
    print("- 场景C-HTTPS：固定IP（HTTPS Proxy-Tunnel，需自定义HTTPAdapter支持）")
    print("\n✅ requests 支持HTTPS Proxy-Tunnel：通过自定义HTTPAdapter.proxy_headers()方法")


if __name__ == '__main__':
    main()
