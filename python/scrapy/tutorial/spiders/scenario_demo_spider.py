#!/usr/bin/env python3
"""
16YUN 隧道代理：Scrapy 四种场景演示Spider

四种场景说明：
- 场景A（强制新建连接）：每次请求强制创建新的连接，IP会发生变化
- 场景B（Keep-Alive保持）：复用TCP连接，同一个Session内多次请求保持相同IP
- 场景C-HTTP（HTTP Proxy-Tunnel）：通过Proxy-Tunnel头固定IP（HTTP目标）
- 场景C-HTTPS（HTTPS Proxy-Tunnel）：通过Proxy-Tunnel头固定IP（HTTPS目标）

注意：Scrapy框架特性导致主要支持场景B（Keep-Alive会话保持），
其他场景通过中间件配置实现类似效果
"""
import scrapy
import os
import random
import json


class ScenarioDemoSpider(scrapy.Spider):
    """四种场景演示Spider"""
    name = "scenario_demo"
    
    # 控制并发和延迟，确保场景效果明显
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,  # 串行请求，便于观察效果
        'DOWNLOAD_DELAY': 1,       # 请求间隔1秒
        'RANDOMIZE_DOWNLOAD_DELAY': False,  # 固定延迟
    }

    def start_requests(self):
        """生成四种场景的请求"""
        print("=" * 60)
        print("16YUN 隧道代理 - Scrapy 四种场景演示")
        print("=" * 60)
        
        # 显示当前配置
        host = os.getenv('PROXY_HOST', 't.16yun.cn')
        port = os.getenv('PROXY_PORT', '31111')
        user = os.getenv('PROXY_USERNAME') or os.getenv('PROXY_USER') or 'username'
        tunnel = os.getenv('PROXY_TUNNEL', '')
        target = os.getenv('TARGET_URL', 'https://httpbin.org/ip')
        
        print(f"代理服务器: {host}:{port}")
        print(f"认证用户: {user}")
        print(f"目标URL: {target}")
        print(f"Proxy-Tunnel: {tunnel or '(自动生成)'}")
        print("=" * 60)
        
        # 场景A：强制新建连接（3次请求）
        for i in range(3):
            yield scrapy.Request(
                url=target,
                callback=self.parse_scenario_a,
                meta={
                    'scenario': 'A',
                    'request_num': i + 1,
                    'force_new_connection': True,  # 标记强制新建连接
                },
                dont_filter=True  # 允许重复URL
            )
        
        # 场景B：Keep-Alive会话保持（3次请求）
        for i in range(3):
            yield scrapy.Request(
                url=target,
                callback=self.parse_scenario_b,
                meta={
                    'scenario': 'B',
                    'request_num': i + 1,
                    'keep_alive': True,  # 标记保持连接
                },
                dont_filter=True
            )
        
        # 场景C-HTTP：HTTP Proxy-Tunnel固定IP（3次请求）
        target_http = "http://httpbin.org/ip"
        for i in range(3):
            yield scrapy.Request(
                url=target_http,
                callback=self.parse_scenario_c_http,
                meta={
                    'scenario': 'C-HTTP',
                    'request_num': i + 1,
                    'proxy_tunnel_http': True,  # 标记HTTP Proxy-Tunnel
                },
                dont_filter=True
            )
        
        # 场景C-HTTPS：HTTPS Proxy-Tunnel固定IP（3次请求）
        for i in range(3):
            yield scrapy.Request(
                url=target,
                callback=self.parse_scenario_c_https,
                meta={
                    'scenario': 'C-HTTPS',
                    'request_num': i + 1,
                    'proxy_tunnel_https': True,  # 标记HTTPS Proxy-Tunnel
                },
                dont_filter=True
            )

    def parse_scenario_a(self, response):
        """解析场景A的响应"""
        self._parse_and_log(response, "场景A：强制新建连接")

    def parse_scenario_b(self, response):
        """解析场景B的响应"""
        self._parse_and_log(response, "场景B：Keep-Alive会话保持")

    def parse_scenario_c_http(self, response):
        """解析场景C-HTTP的响应"""
        self._parse_and_log(response, "场景C-HTTP：HTTP Proxy-Tunnel固定IP")

    def parse_scenario_c_https(self, response):
        """解析场景C-HTTPS的响应"""
        self._parse_and_log(response, "场景C-HTTPS：HTTPS Proxy-Tunnel固定IP")

    def _parse_and_log(self, response, scenario_name):
        """解析响应并记录IP信息"""
        try:
            data = json.loads(response.text)
            origin_ip = data.get('origin', 'N/A')
            request_num = response.meta.get('request_num', 0)
            
            # 获取使用的Proxy-Tunnel值（如果有）
            proxy_tunnel = response.request.headers.get('Proxy-Tunnel', b'').decode('utf-8')
            tunnel_info = f" (Proxy-Tunnel: {proxy_tunnel})" if proxy_tunnel else ""
            
            self.logger.info(f"=== {scenario_name} ===")
            self.logger.info(f"  请求 {request_num}: IP = {origin_ip}{tunnel_info}")
            
            # 如果是最后一个请求，输出场景总结
            if request_num == 3:
                self._print_scenario_summary(response.meta.get('scenario', ''))
                
        except Exception as e:
            self.logger.error(f"解析响应失败: {e}")

    def _print_scenario_summary(self, scenario):
        """输出场景总结"""
        if scenario == 'A':
            self.logger.info("场景A总结：每次请求强制新建连接，IP应该不同")
            self.logger.info("")
        elif scenario == 'B':
            self.logger.info("场景B总结：复用连接，多次请求应该保持相同IP")
            self.logger.info("")
        elif scenario == 'C-HTTP':
            self.logger.info("场景C-HTTP总结：通过Proxy-Tunnel头固定IP（HTTP目标）")
            self.logger.info("")
        elif scenario == 'C-HTTPS':
            self.logger.info("场景C-HTTPS总结：通过Proxy-Tunnel头固定IP（HTTPS目标）")
            self.logger.info("=" * 60)
            self.logger.info("场景对比总结：")
            self.logger.info("- 场景A：每次不同IP（强制新建连接）")
            self.logger.info("- 场景B：多次相同IP（Keep-Alive复用连接）")
            self.logger.info("- 场景C-HTTP：固定IP（HTTP Proxy-Tunnel）")
            self.logger.info("- 场景C-HTTPS：固定IP（HTTPS Proxy-Tunnel）")
            self.logger.info("")
            self.logger.info("⚠️  Scrapy注意事项：")
            self.logger.info("- Scrapy主要适用于场景B（Keep-Alive会话保持）")
            self.logger.info("- 场景A需要通过中间件控制连接池实现")
            self.logger.info("- 场景C需要在中间件中添加Proxy-Tunnel头")
            self.logger.info("- ❌ Scrapy不支持HTTPS Proxy-Tunnel（无法在CONNECT阶段注入头）")

    def closed(self, reason):
        """Spider关闭时的回调"""
        self.logger.info("=" * 60)
        self.logger.info("Scrapy四种场景演示完成")
        self.logger.info("=" * 60)
