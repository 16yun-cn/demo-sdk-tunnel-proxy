"""
16YUN 隧道代理：Scrapy 四种场景中间件

支持四种代理使用场景：
- 场景A（强制新建连接）：每次请求强制创建新的连接
- 场景B（Keep-Alive保持）：复用TCP连接，保持相同IP
- 场景C-HTTP（HTTP Proxy-Tunnel）：通过Proxy-Tunnel头固定IP（HTTP目标）
- 场景C-HTTPS（HTTPS Proxy-Tunnel）：通过Proxy-Tunnel头固定IP（HTTPS目标）

注意：Scrapy框架限制，主要支持场景B和场景C的HTTP目标
"""
import os
import random
from typing import Optional


class ProxyDownloaderMiddleware:
    """代理下载中间件，支持四种场景模式"""
    
    def __init__(self) -> None:
        # 获取代理配置（支持别名兼容）
        self.host = os.getenv("PROXY_HOST", "t.16yun.cn").strip()
        self.port = os.getenv("PROXY_PORT", "31111").strip()
        self.user = (os.getenv("PROXY_USERNAME") or os.getenv("PROXY_USER") or "").strip()
        self.pwd = (os.getenv("PROXY_PASSWORD") or os.getenv("PROXY_PASS") or "").strip()
        self.tunnel = os.getenv("PROXY_TUNNEL", "").strip()
        
        # 生成固定的Proxy-Tunnel种子（用于场景C）
        self.fixed_tunnel_seed = self.tunnel or str(random.randint(1, 10000))

    def process_request(self, request, spider):  # type: ignore[override]
        """处理请求，根据场景类型应用不同的代理策略"""
        
        # 构建代理URL
        if self.user and self.pwd:
            proxy = f"http://{self.user}:{self.pwd}@{self.host}:{self.port}"
        else:
            proxy = f"http://{self.host}:{self.port}"
        
        # 设置代理
        request.meta["proxy"] = proxy
        
        # 根据请求meta中的场景标记应用不同策略
        scenario = request.meta.get('scenario', 'B')  # 默认场景B
        
        if request.meta.get('force_new_connection', False):
            # 场景A：强制新建连接
            self._apply_scenario_a(request)
        elif request.meta.get('proxy_tunnel_http', False):
            # 场景C-HTTP：HTTP Proxy-Tunnel固定IP
            self._apply_scenario_c_http(request)
        elif request.meta.get('proxy_tunnel_https', False):
            # 场景C-HTTPS：HTTPS Proxy-Tunnel固定IP（有限支持）
            self._apply_scenario_c_https(request)
        else:
            # 场景B：Keep-Alive会话保持（默认）
            self._apply_scenario_b(request)
        
        return None

    def _apply_scenario_a(self, request):
        """
        场景A：强制新建连接
        技术实现：尝试禁用连接复用（Scrapy框架限制）
        效果：每次请求尽可能分配不同的出口IP
        """
        # Scrapy框架限制，无法完全控制连接池
        # 这里通过添加随机头来尝试区分请求
        request.headers.setdefault("Connection", "close")
        request.headers.setdefault("Cache-Control", "no-cache")
        # 添加随机标识来区分请求
        request.headers.setdefault("X-Request-ID", str(random.randint(1, 100000)))
        
        # 移除Keep-Alive相关头
        if "Proxy-Connection" in request.headers:
            del request.headers["Proxy-Connection"]

    def _apply_scenario_b(self, request):
        """
        场景B：Keep-Alive会话保持
        技术实现：启用连接复用和Keep-Alive
        效果：多次请求复用TCP连接，保持相同的出口IP
        """
        request.headers.setdefault("Connection", "keep-alive")
        request.headers.setdefault("Proxy-Connection", "keep-alive")
        # 启用HTTP/1.1持久连接
        request.headers.setdefault("Keep-Alive", "timeout=60, max=100")

    def _apply_scenario_c_http(self, request):
        """
        场景C-HTTP：HTTP Proxy-Tunnel固定IP
        技术实现：在请求头中添加固定的Proxy-Tunnel
        效果：通过Proxy-Tunnel头固定出口IP（HTTP目标）
        """
        # 添加固定的Proxy-Tunnel头
        request.headers["Proxy-Tunnel"] = self.fixed_tunnel_seed
        # 保持连接以确保Proxy-Tunnel生效
        request.headers.setdefault("Connection", "keep-alive")
        request.headers.setdefault("Proxy-Connection", "keep-alive")

    def _apply_scenario_c_https(self, request):
        """
        场景C-HTTPS：HTTPS Proxy-Tunnel固定IP
        技术实现：在请求头中添加Proxy-Tunnel（有限支持）
        效果：尝试通过Proxy-Tunnel头固定出口IP（HTTPS目标）
        注意：Scrapy无法在CONNECT阶段注入头，该场景支持有限
        """
        # ⚠️ 注意：这里只是在应用层添加Proxy-Tunnel头
        # 对于HTTPS目标，Scrapy无法在CONNECT阶段注入该头
        # 实际效果可能不如预期
        request.headers["Proxy-Tunnel"] = self.fixed_tunnel_seed
        request.headers.setdefault("Connection", "keep-alive")
        request.headers.setdefault("Proxy-Connection", "keep-alive")

    def process_exception(self, request, exception, spider):  # type: ignore[override]
        """处理异常"""
        # 记录代理相关异常，便于调试
        spider.logger.warning(f"代理请求异常: {exception}")
        return None

