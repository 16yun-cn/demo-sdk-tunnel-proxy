// 16YUN(亿牛云) Go net/http 隧道代理演示
//
// 本示例演示四种隧道代理使用场景：
// - 场景A：每次新建连接（强制IP切换）
// - 场景B：Keep-Alive会话保持（相同IP）
// - 场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标）
// - 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标）✅支持
//
// 技术特点：
// - Go net/http原生支持通过Transport.ProxyConnectHeader在CONNECT阶段添加自定义头
// - 完整的四种场景实现，覆盖所有代理使用模式
// - 详细的中文注释和技术原理说明
package main

import (
	"crypto/tls"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"math/rand"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"time"
)

// getenv 获取环境变量，支持默认值
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
	return url.Parse(fmt.Sprintf("http://%s:%s", host, port))
}

// buildProxyAuth 构建代理认证头
func buildProxyAuth() string {
	user := getenv("PROXY_USERNAME", "username")
	if userAlias := getenv("PROXY_USER", ""); userAlias != "" {
		user = userAlias
	}

	pass := getenv("PROXY_PASSWORD", "password")
	if passAlias := getenv("PROXY_PASS", ""); passAlias != "" {
		pass = passAlias
	}

	basic := base64.StdEncoding.EncodeToString([]byte(user + ":" + pass))
	return "Basic " + basic
}

// scenarioAForceNewConnection 场景A：每次新建连接（强制IP切换）
//
// 技术原理：每次请求创建新的Transport和Client，设置DisableKeepAlives，强制断开连接
// 适用场合：需要每个请求都使用不同IP的场景
func scenarioAForceNewConnection() {
	fmt.Println("\n=== 场景A：每次新建连接（强制IP切换） ===")
	fmt.Println("技术原理：每次请求创建新的Transport和Client，设置DisableKeepAlives，强制断开连接")
	fmt.Println("适用场合：需要每个请求都使用不同IP的场景")

	proxyURL, _ := buildProxyURL()
	proxyAuth := buildProxyAuth()
	targetURL := getenv("TARGET_URL", "https://httpbin.org/ip")

	for i := 1; i <= 2; i++ {
		// 每次创建新的Transport和Client
		tr := &http.Transport{
			Proxy:               http.ProxyURL(proxyURL),
			TLSClientConfig:     &tls.Config{InsecureSkipVerify: false},
			DisableKeepAlives:   true, // 关键：禁用Keep-Alive
			MaxIdleConns:        0,    // 不复用连接
			IdleConnTimeout:     1 * time.Second,
			TLSHandshakeTimeout: 10 * time.Second,
		}
		client := &http.Client{
			Transport: tr,
			Timeout:   15 * time.Second,
		}

		req, _ := http.NewRequest("GET", targetURL, nil)
		req.Header.Set("Connection", "close")
		req.Header.Set("Proxy-Connection", "close")
		req.Header.Set("Proxy-Authorization", proxyAuth)

		resp, err := client.Do(req)
		if err != nil {
			fmt.Printf("请求 %d 失败: %v\n", i, err)
			continue
		}

		body, _ := io.ReadAll(resp.Body)
		resp.Body.Close()

		if resp.StatusCode == 200 {
			ip := extractIP(body)
			fmt.Printf("请求 %d - IP: %s\n", i, ip)
		} else {
			fmt.Printf("请求 %d 失败 - 状态码: %d\n", i, resp.StatusCode)
		}
	}
}

// scenarioBKeepAlive 场景B：Keep-Alive会话保持（相同IP）
//
// 技术原理：复用同一个Client和Transport，启用Keep-Alive，在代理有效期内使用相同IP
// 适用场合：需要多个请求保持相同IP的场景，如登录流程
func scenarioBKeepAlive() {
	fmt.Println("\n=== 场景B：Keep-Alive会话保持（相同IP） ===")
	fmt.Println("技术原理：复用同一个Client和Transport，启用Keep-Alive，在代理有效期内使用相同IP")
	fmt.Println("适用场合：需要多个请求保持相同IP的场景，如登录流程")

	proxyURL, _ := buildProxyURL()
	proxyAuth := buildProxyAuth()
	targetURL := getenv("TARGET_URL", "https://httpbin.org/ip")

	// 创建一个持久的Transport和Client
	tr := &http.Transport{
		Proxy:               http.ProxyURL(proxyURL),
		TLSClientConfig:     &tls.Config{InsecureSkipVerify: false},
		DisableKeepAlives:   false, // 启用Keep-Alive
		MaxIdleConns:        10,
		IdleConnTimeout:     30 * time.Second,
		TLSHandshakeTimeout: 10 * time.Second,
	}
	client := &http.Client{
		Transport: tr,
		Timeout:   15 * time.Second,
	}

	for i := 1; i <= 2; i++ {
		req, _ := http.NewRequest("GET", targetURL, nil)
		req.Header.Set("Connection", "keep-alive")
		req.Header.Set("Proxy-Connection", "keep-alive")
		req.Header.Set("Proxy-Authorization", proxyAuth)

		resp, err := client.Do(req)
		if err != nil {
			fmt.Printf("请求 %d 失败: %v\n", i, err)
			continue
		}

		body, _ := io.ReadAll(resp.Body)
		resp.Body.Close()

		if resp.StatusCode == 200 {
			ip := extractIP(body)
			fmt.Printf("请求 %d - IP: %s\n", i, ip)
		} else {
			fmt.Printf("请求 %d 失败 - 状态码: %d\n", i, resp.StatusCode)
		}
	}
}

// scenarioCProxyTunnelHttp 场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标）
//
// 技术原理：在HTTP请求头中添加Proxy-Tunnel，相同值保持相同IP
// 适用场合：需要自定义控制IP切换的HTTP访问场景
func scenarioCProxyTunnelHttp() {
	fmt.Println("\n=== 场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标） ===")
	fmt.Println("技术原理：在HTTP请求头中添加Proxy-Tunnel，相同值保持相同IP")
	fmt.Println("适用场合：需要自定义控制IP切换的HTTP访问场景")

	proxyURL, _ := buildProxyURL()
	proxyAuth := buildProxyAuth()
	tunnelValue := getenv("PROXY_TUNNEL", "")

	// 如果没有设置PROXY_TUNNEL，生成一个随机值
	if tunnelValue == "" {
		rand.Seed(time.Now().UnixNano())
		tunnelValue = strconv.Itoa(rand.Intn(10000) + 1)
	}

	fmt.Printf("使用Proxy-Tunnel值: %s\n", tunnelValue)

	tr := &http.Transport{
		Proxy:               http.ProxyURL(proxyURL),
		TLSClientConfig:     &tls.Config{InsecureSkipVerify: false},
		DisableKeepAlives:   false,
		MaxIdleConns:        10,
		IdleConnTimeout:     30 * time.Second,
		TLSHandshakeTimeout: 10 * time.Second,
	}
	client := &http.Client{
		Transport: tr,
		Timeout:   15 * time.Second,
	}

	for i := 1; i <= 2; i++ {
		req, _ := http.NewRequest("GET", "http://httpbin.org/ip", nil) // HTTP目标
		req.Header.Set("Proxy-Tunnel", tunnelValue)
		req.Header.Set("Connection", "keep-alive")
		req.Header.Set("Proxy-Authorization", proxyAuth)

		resp, err := client.Do(req)
		if err != nil {
			fmt.Printf("请求 %d 失败: %v\n", i, err)
			continue
		}

		body, _ := io.ReadAll(resp.Body)
		resp.Body.Close()

		if resp.StatusCode == 200 {
			ip := extractIP(body)
			fmt.Printf("请求 %d - IP: %s\n", i, ip)
		} else {
			fmt.Printf("请求 %d 失败 - 状态码: %d\n", i, resp.StatusCode)
		}
	}
}

// scenarioCProxyTunnelHttps 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标）
//
// 技术原理：Go net/http通过Transport.ProxyConnectHeader在CONNECT阶段携带Proxy-Tunnel头
// 适用场合：需要自定义控制IP切换的HTTPS访问场景
func scenarioCProxyTunnelHttps() {
	fmt.Println("\n=== 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标） ===")
	fmt.Println("技术原理：Go net/http通过Transport.ProxyConnectHeader在CONNECT阶段携带Proxy-Tunnel头")
	fmt.Println("适用场合：需要自定义控制IP切换的HTTPS访问场景")

	proxyURL, _ := buildProxyURL()
	proxyAuth := buildProxyAuth()
	tunnelValue := getenv("PROXY_TUNNEL", "")

	// 如果没有设置PROXY_TUNNEL，生成一个随机值
	if tunnelValue == "" {
		rand.Seed(time.Now().UnixNano())
		tunnelValue = strconv.Itoa(rand.Intn(10000) + 1)
	}

	fmt.Printf("使用Proxy-Tunnel值: %s\n", tunnelValue)

	// 设置CONNECT阶段的头（关键实现）
	connectHeaders := http.Header{}
	connectHeaders.Set("Proxy-Authorization", proxyAuth)
	connectHeaders.Set("Proxy-Tunnel", tunnelValue) // 这会在CONNECT时发送

	tr := &http.Transport{
		Proxy:               http.ProxyURL(proxyURL),
		TLSClientConfig:     &tls.Config{InsecureSkipVerify: false},
		ProxyConnectHeader:  connectHeaders, // 关键：CONNECT阶段的头
		DisableKeepAlives:   false,
		MaxIdleConns:        10,
		IdleConnTimeout:     30 * time.Second,
		TLSHandshakeTimeout: 10 * time.Second,
	}
	client := &http.Client{
		Transport: tr,
		Timeout:   15 * time.Second,
	}

	for i := 1; i <= 2; i++ {
		req, _ := http.NewRequest("GET", "https://httpbin.org/ip", nil) // HTTPS目标

		resp, err := client.Do(req)
		if err != nil {
			fmt.Printf("请求 %d 失败: %v\n", i, err)
			continue
		}

		body, _ := io.ReadAll(resp.Body)
		resp.Body.Close()

		if resp.StatusCode == 200 {
			ip := extractIP(body)
			fmt.Printf("请求 %d - IP: %s\n", i, ip)
		} else {
			fmt.Printf("请求 %d 失败 - 状态码: %d\n", i, resp.StatusCode)
		}
	}
}

func main() {
	fmt.Println("16YUN(亿牛云) Go net/http 隧道代理演示")
	fmt.Println("支持的环境变量：")
	fmt.Println("  PROXY_HOST (默认: t.16yun.cn)")
	fmt.Println("  PROXY_PORT (默认: 31111)")
	fmt.Println("  PROXY_USERNAME / PROXY_USER (默认: user)")
	fmt.Println("  PROXY_PASSWORD / PROXY_PASS (默认: password)")
	fmt.Println("  PROXY_TUNNEL (可选: 自定义tunnel值)")
	fmt.Println("  TARGET_URL (默认: https://httpbin.org/ip)")

	// 执行四种场景演示
	scenarioAForceNewConnection()
	scenarioBKeepAlive()
	scenarioCProxyTunnelHttp()
	scenarioCProxyTunnelHttps()

	fmt.Println("\n演示完成！")
	fmt.Println("注意：Go net/http原生支持HTTPS下的Proxy-Tunnel（通过Transport.ProxyConnectHeader）")
}
