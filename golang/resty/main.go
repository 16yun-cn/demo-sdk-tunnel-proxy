// 16YUN(亿牛云) Go Resty 隧道代理演示
//
// 本示例演示四种隧道代理使用场景：
// - 场景A：每次新建连接（强制IP切换）
// - 场景B：Keep-Alive会话保持（相同IP）
// - 场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标）
// - 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标）✅支持
//
// 技术特点：
// - Resty基于Go net/http，原生支持通过底层Transport设置ProxyConnectHeader
// - 完整的四种场景实现，覆盖所有代理使用模式
// - 详细的中文注释和技术原理说明
package main

import (
	"crypto/tls"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"os"
	"time"

	"github.com/go-resty/resty/v2"
)

// getenv 获取环境变量，支持默认值和别名
func getenv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// extractIP 从httpbin响应中提取IP地址
func extractIP(body []byte) string {
	var data map[string]interface{}
	if err := json.Unmarshal(body, &data); err != nil {
		return "解析失败"
	}
	if origin, ok := data["origin"].(string); ok {
		return origin
	}
	return "未知IP"
}

// buildProxyURL 构建代理URL
func buildProxyURL() (*url.URL, error) {
	host := getenv("PROXY_HOST", "t.16yun.cn")
	port := getenv("PROXY_PORT", "31111")
	user := getenv("PROXY_USERNAME", getenv("PROXY_USER", "user"))
	pass := getenv("PROXY_PASSWORD", getenv("PROXY_PASS", "password"))

	proxyURL := fmt.Sprintf("http://%s:%s@%s:%s", user, pass, host, port)
	return url.Parse(proxyURL)
}

// scenarioAForceNewConnection 场景A：每次新建连接（强制IP切换）
//
// 技术原理：
// - 每次请求创建新的Resty客户端实例
// - 禁用连接池和Keep-Alive
// - 这样确保每次请求都建立新的TCP连接，从而获得不同的出口IP
//
// 适用场合：
// - 需要每个请求都使用不同IP的爬虫场景
// - 避免目标网站检测到连续请求来自同一IP
// - IP轮换要求较高的场景
func scenarioAForceNewConnection() {
	fmt.Println("\n=== 场景A：每次新建连接（强制IP切换） ===")
	fmt.Println("技术原理：每次请求创建新的Resty客户端，禁用连接池")
	fmt.Println("适用场合：需要每个请求都使用不同IP的场景")

	proxyURL, err := buildProxyURL()
	if err != nil {
		fmt.Printf("代理URL解析失败: %v\n", err)
		return
	}

	targetURL := getenv("TARGET_URL", "https://httpbin.org/ip")

	for i := 1; i <= 3; i++ {
		// 每次创建新的客户端实例
		client := resty.New()

		// 配置代理
		client.SetProxy(proxyURL.String())

		// 禁用连接池，强制每次新建连接
		client.SetTransport(&http.Transport{
			Proxy: http.ProxyURL(proxyURL),
			TLSClientConfig: &tls.Config{
				InsecureSkipVerify: true,
			},
			DisableKeepAlives:   true, // 关键：禁用Keep-Alive
			MaxIdleConns:        0,    // 关键：不保持空闲连接
			MaxIdleConnsPerHost: 0,    // 关键：每个host不保持空闲连接
		})

		// 设置超时
		client.SetTimeout(15 * time.Second)

		// 添加强制关闭连接的头部
		resp, err := client.R().
			SetHeader("Connection", "close").
			SetHeader("Proxy-Connection", "close").
			Get(targetURL)

		if err != nil {
			fmt.Printf("请求 %d: 错误 - %v\n", i, err)
			continue
		}

		ip := extractIP(resp.Body())
		fmt.Printf("请求 %d: %d - %s\n", i, resp.StatusCode(), ip)

		// 短暂延迟确保连接完全关闭
		time.Sleep(500 * time.Millisecond)
	}
}

// scenarioBKeepAlive 场景B：Keep-Alive会话保持（相同IP）
//
// 技术原理：
// - 使用同一个Resty客户端实例进行多次请求
// - 启用连接池和Keep-Alive
// - 代理会复用相同的TCP连接，保持相同的出口IP
//
// 适用场合：
// - 需要维持登录状态的连续操作
// - 模拟真实用户的浏览行为
// - 需要在会话期间保持相同IP的场景
func scenarioBKeepAlive() {
	fmt.Println("\n=== 场景B：Keep-Alive会话保持（相同IP） ===")
	fmt.Println("技术原理：使用同一个Resty客户端，保持TCP连接和Keep-Alive")
	fmt.Println("适用场合：需要在会话期间保持相同IP的场景")

	proxyURL, err := buildProxyURL()
	if err != nil {
		fmt.Printf("代理URL解析失败: %v\n", err)
		return
	}

	targetURL := getenv("TARGET_URL", "https://httpbin.org/ip")

	// 创建一个客户端实例，用于所有请求
	client := resty.New()

	// 配置代理
	client.SetProxy(proxyURL.String())

	// 启用连接池，保持连接
	client.SetTransport(&http.Transport{
		Proxy: http.ProxyURL(proxyURL),
		TLSClientConfig: &tls.Config{
			InsecureSkipVerify: true,
		},
		DisableKeepAlives:   false, // 关键：启用Keep-Alive
		MaxIdleConns:        10,    // 关键：保持空闲连接
		MaxIdleConnsPerHost: 10,    // 关键：每个host保持空闲连接
		IdleConnTimeout:     90 * time.Second,
	})

	// 设置超时
	client.SetTimeout(15 * time.Second)

	for i := 1; i <= 3; i++ {
		resp, err := client.R().
			SetHeader("Connection", "keep-alive").
			SetHeader("Proxy-Connection", "keep-alive").
			Get(targetURL)

		if err != nil {
			fmt.Printf("请求 %d: 错误 - %v\n", i, err)
			continue
		}

		ip := extractIP(resp.Body())
		fmt.Printf("请求 %d: %d - %s\n", i, resp.StatusCode(), ip)

		// 短暂延迟但保持连接
		time.Sleep(200 * time.Millisecond)
	}
}

// scenarioCProxyTunnelHttp 场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标）
//
// 技术原理：
// - 在HTTP请求头中添加Proxy-Tunnel标识
// - 代理服务器识别相同的Proxy-Tunnel值，分配固定的出口IP
// - 适用于HTTP目标URL
//
// 适用场合：
// - 需要固定IP进行API调用的场景
// - 需要IP会话管理的业务逻辑
// - 确保同一业务流程使用相同IP
func scenarioCProxyTunnelHttp() {
	fmt.Println("\n=== 场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标） ===")
	fmt.Println("技术原理：在HTTP请求头中添加Proxy-Tunnel标识")
	fmt.Println("适用场合：需要使用固定IP访问HTTP目标的场景")

	proxyURL, err := buildProxyURL()
	if err != nil {
		fmt.Printf("代理URL解析失败: %v\n", err)
		return
	}

	// HTTP目标（用于Proxy-Tunnel演示）
	httpTargetURL := "http://httpbin.org/ip"
	tunnelID := getenv("PROXY_TUNNEL", "golang-resty-demo-12345")

	fmt.Printf("Proxy-Tunnel值: %s\n", tunnelID)

	// 创建客户端实例，保持会话
	client := resty.New()

	// 配置代理
	client.SetProxy(proxyURL.String())

	// 保持连接以维持Proxy-Tunnel会话
	client.SetTransport(&http.Transport{
		Proxy: http.ProxyURL(proxyURL),
		TLSClientConfig: &tls.Config{
			InsecureSkipVerify: true,
		},
		DisableKeepAlives:   false,
		MaxIdleConns:        10,
		MaxIdleConnsPerHost: 10,
		IdleConnTimeout:     90 * time.Second,
	})

	// 设置超时
	client.SetTimeout(15 * time.Second)

	for i := 1; i <= 3; i++ {
		resp, err := client.R().
			SetHeader("Proxy-Tunnel", tunnelID). // 关键：添加Proxy-Tunnel头（仅对HTTP目标有效）
			SetHeader("Connection", "keep-alive").
			SetHeader("Proxy-Connection", "keep-alive").
			Get(httpTargetURL)

		if err != nil {
			fmt.Printf("请求 %d: 错误 - %v\n", i, err)
			continue
		}

		ip := extractIP(resp.Body())
		fmt.Printf("请求 %d: %d - %s\n", i, resp.StatusCode(), ip)

		time.Sleep(200 * time.Millisecond)
	}
}

// scenarioCProxyTunnelHttps 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标）
//
// 技术原理：
// - 使用Go net/http的Transport.ProxyConnectHeader功能
// - 在HTTPS CONNECT握手阶段添加Proxy-Tunnel头
// - Resty基于net/http，可以通过自定义Transport实现
//
// 适用场合：
// - 需要固定IP访问HTTPS网站的场景
// - HTTPS API调用需要IP一致性
// - 安全要求较高的业务场景
func scenarioCProxyTunnelHttps() {
	fmt.Println("\n=== 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标） ===")
	fmt.Println("技术原理：通过Transport.ProxyConnectHeader在CONNECT阶段添加Proxy-Tunnel头")
	fmt.Println("适用场合：需要使用固定IP访问HTTPS目标的场景")

	proxyURL, err := buildProxyURL()
	if err != nil {
		fmt.Printf("代理URL解析失败: %v\n", err)
		return
	}

	targetURL := getenv("TARGET_URL", "https://httpbin.org/ip")
	tunnelID := getenv("PROXY_TUNNEL", "golang-resty-demo-12345")

	fmt.Printf("✅ Resty基于Go net/http，支持HTTPS Proxy-Tunnel\n")
	fmt.Printf("Proxy-Tunnel值: %s\n", tunnelID)

	// 创建客户端实例
	client := resty.New()

	// 配置支持HTTPS Proxy-Tunnel的Transport
	transport := &http.Transport{
		Proxy: http.ProxyURL(proxyURL),
		TLSClientConfig: &tls.Config{
			InsecureSkipVerify: true,
		},
		// 关键：在CONNECT阶段添加自定义头
		ProxyConnectHeader: http.Header{
			"Proxy-Tunnel": []string{tunnelID}, // 关键：这个头会在CONNECT阶段发送
		},
		DisableKeepAlives:   false,
		MaxIdleConns:        10,
		MaxIdleConnsPerHost: 10,
		IdleConnTimeout:     90 * time.Second,
	}

	client.SetTransport(transport)
	client.SetTimeout(15 * time.Second)

	for i := 1; i <= 3; i++ {
		resp, err := client.R().
			SetHeader("Connection", "keep-alive").
			SetHeader("Proxy-Connection", "keep-alive").
			Get(targetURL)

		if err != nil {
			fmt.Printf("请求 %d: 错误 - %v\n", i, err)
			continue
		}

		ip := extractIP(resp.Body())
		fmt.Printf("请求 %d: %d - %s\n", i, resp.StatusCode(), ip)

		time.Sleep(200 * time.Millisecond)
	}
}

func main() {
	fmt.Println("=== Go Resty 隧道代理四种场景演示 ===")

	// 显示配置信息
	host := getenv("PROXY_HOST", "t.16yun.cn")
	port := getenv("PROXY_PORT", "31111")
	user := getenv("PROXY_USERNAME", getenv("PROXY_USER", "user"))
	tunnel := getenv("PROXY_TUNNEL", "golang-resty-demo-12345")

	fmt.Printf("代理服务器: %s:%s\n", host, port)
	fmt.Printf("代理用户: %s\n", user)
	fmt.Printf("Proxy-Tunnel: %s\n", tunnel)

	// 执行四种场景演示
	scenarioAForceNewConnection()
	scenarioBKeepAlive()
	scenarioCProxyTunnelHttp()
	scenarioCProxyTunnelHttps()

	fmt.Println("\n=== 所有场景演示完成 ===")
}
