/*!
 * Rust isahc 隧道代理四种场景演示
 * 基于16YUN爬虫代理服务的完整实现
 * 
 * 注意: isahc 1.7 不支持 proxy_headers，无法在 CONNECT 阶段添加自定义头
 * 因此 HTTPS Proxy-Tunnel 场景无法实现，仅演示 HTTP 场景
 */

use anyhow::{anyhow, Context, Result};
use isahc::{prelude::*, HttpClient, Request};
use serde_json::Value;
use std::env;
use std::time::Duration;

// 代理配置信息
#[derive(Debug, Clone)]
struct ProxyConfig {
    host: String,
    port: String,
    user: String,
    pass: String,
    tunnel: String,
}

impl ProxyConfig {
    fn from_env() -> Result<Self> {
        let host = env::var("PROXY_HOST").unwrap_or_else(|_| "t.16yun.cn".to_string());
        let port = env::var("PROXY_PORT").unwrap_or_else(|_| "31111".to_string());
        let user = env::var("PROXY_USERNAME")
            .or_else(|_| env::var("PROXY_USER"))
            .map_err(|_| anyhow!("Missing PROXY_USERNAME or PROXY_USER"))?;
        let pass = env::var("PROXY_PASSWORD")
            .or_else(|_| env::var("PROXY_PASS"))
            .map_err(|_| anyhow!("Missing PROXY_PASSWORD or PROXY_PASS"))?;
        let tunnel = env::var("PROXY_TUNNEL").unwrap_or_else(|_| "rust-isahc-demo-12345".to_string());

        if user.is_empty() || pass.is_empty() {
            return Err(anyhow!("Empty PROXY_USERNAME/PROXY_PASSWORD"));
        }

        Ok(ProxyConfig {
            host,
            port,
            user,
            pass,
            tunnel,
        })
    }

    fn proxy_url(&self) -> String {
        format!("http://{}:{}@{}:{}", self.user, self.pass, self.host, self.port)
    }
}

// 从响应中提取IP地址
fn extract_ip(response: &str) -> Result<String> {
    let json: Value = serde_json::from_str(response)
        .context("Failed to parse JSON response")?;
    
    json.get("origin")
        .and_then(|v| v.as_str())
        .map(String::from)
        .ok_or_else(|| anyhow!("No 'origin' field found in response"))
}

/// 场景A：强制新建连接（每次不同IP）
fn scenario_a_force_new_connection(config: &ProxyConfig) -> Result<()> {
    println!("\n=== 场景A：强制新建连接（强制IP切换） ===");
    println!("技术原理：每次请求创建新的HttpClient实例，禁用连接复用");
    println!("适用场合：需要每个请求都使用不同IP的场景");

    let target_url = env::var("TARGET_URL").unwrap_or_else(|_| "http://httpbin.org/ip".to_string());
    let proxy_url = config.proxy_url();

    for i in 1..=3 {
        // 每次创建新的HttpClient实例
        let client = HttpClient::builder()
            .proxy(Some(proxy_url.parse()?))
            .timeout(Duration::from_secs(15))
            .tcp_keepalive(Duration::from_secs(0))  // 修复: 使用 Duration
            .build()?;

        let request = Request::get(&target_url)
            .header("Connection", "close")
            .header("Proxy-Connection", "close")
            .body(())?;

        match client.send(request) {
            Ok(mut response) => {
                let body = response.text()?;  // 同步调用
                match extract_ip(&body) {
                    Ok(ip) => println!("请求 {}: {} - {}", i, response.status(), ip),
                    Err(_) => println!("请求 {}: {} - IP解析失败", i, response.status()),
                }
            }
            Err(e) => println!("请求 {}: 错误 - {}", i, e),
        }

        std::thread::sleep(Duration::from_millis(500));
    }

    Ok(())
}

/// 场景B：Keep-Alive会话保持（相同IP）
fn scenario_b_keep_alive(config: &ProxyConfig) -> Result<()> {
    println!("\n=== 场景B：Keep-Alive会话保持（相同IP） ===");
    println!("技术原理：使用同一个HttpClient实例，保持TCP连接和Keep-Alive");
    println!("适用场合：需要在会话期间保持相同IP的场景");

    let target_url = env::var("TARGET_URL").unwrap_or_else(|_| "http://httpbin.org/ip".to_string());
    let proxy_url = config.proxy_url();

    let client = HttpClient::builder()
        .proxy(Some(proxy_url.parse()?))
        .timeout(Duration::from_secs(15))
        .tcp_keepalive(Duration::from_secs(30))  // 修复: 使用 Duration
        .build()?;

    for i in 1..=3 {
        let request = Request::get(&target_url)
            .header("Connection", "keep-alive")
            .header("Proxy-Connection", "keep-alive")
            .body(())?;

        match client.send(request) {
            Ok(mut response) => {
                let body = response.text()?;
                match extract_ip(&body) {
                    Ok(ip) => println!("请求 {}: {} - {}", i, response.status(), ip),
                    Err(_) => println!("请求 {}: {} - IP解析失败", i, response.status()),
                }
            }
            Err(e) => println!("请求 {}: 错误 - {}", i, e),
        }

        std::thread::sleep(Duration::from_millis(200));
    }

    Ok(())
}

/// 场景C：Proxy-Tunnel固定IP（仅HTTP目标）
fn scenario_c_proxy_tunnel_http(config: &ProxyConfig) -> Result<()> {
    println!("\n=== 场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标） ===");
    println!("技术原理：在HTTP请求头中添加Proxy-Tunnel标识");
    println!("适用场合：需要使用固定IP访问HTTP目标的场景");

    let http_target_url = "http://httpbin.org/ip";
    let proxy_url = config.proxy_url();

    println!("Proxy-Tunnel值: {}", config.tunnel);

    let client = HttpClient::builder()
        .proxy(Some(proxy_url.parse()?))
        .timeout(Duration::from_secs(15))
        .tcp_keepalive(Duration::from_secs(30))
        .build()?;

    for i in 1..=3 {
        let request = Request::get(http_target_url)
            .header("Proxy-Tunnel", &config.tunnel)
            .header("Connection", "keep-alive")
            .header("Proxy-Connection", "keep-alive")
            .body(())?;

        match client.send(request) {
            Ok(mut response) => {
                let body = response.text()?;
                match extract_ip(&body) {
                    Ok(ip) => println!("请求 {}: {} - {}", i, response.status(), ip),
                    Err(_) => println!("请求 {}: {} - IP解析失败", i, response.status()),
                }
            }
            Err(e) => println!("请求 {}: 错误 - {}", i, e),
        }

        std::thread::sleep(Duration::from_millis(200));
    }

    Ok(())
}

fn main() -> Result<()> {
    println!("=== Rust isahc 隧道代理演示 ===");
    println!("⚠️  注意: isahc 1.7 不支持 HTTPS CONNECT 自定义头，仅演示 HTTP 场景");

    let config = ProxyConfig::from_env().context("Failed to load proxy configuration")?;

    println!("代理服务器: {}:{}", config.host, config.port);
    println!("代理用户: {}", config.user);
    println!("Proxy-Tunnel: {}", config.tunnel);

    if let Err(e) = scenario_a_force_new_connection(&config) {
        eprintln!("场景A执行失败: {}", e);
    }

    if let Err(e) = scenario_b_keep_alive(&config) {
        eprintln!("场景B执行失败: {}", e);
    }

    if let Err(e) = scenario_c_proxy_tunnel_http(&config) {
        eprintln!("场景C-HTTP执行失败: {}", e);
    }

    println!("\n=== 所有场景演示完成 ===");

    Ok(())
}
