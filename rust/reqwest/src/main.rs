/*!
 * Rust reqwest 隧道代理四种场景演示
 * 基于16YUN爬虫代理服务的完整实现
 * 
 * 四种场景说明：
 * A. 强制新建连接 - 每次请求建立新连接，获得不同IP
 * B. Keep-Alive会话保持 - 复用TCP连接，保持相同IP  
 * C. Proxy-Tunnel固定IP (HTTP) - 使用Proxy-Tunnel头固定IP访问HTTP目标
 * C. Proxy-Tunnel固定IP (HTTPS) - 使用Proxy-Tunnel头固定IP访问HTTPS目标
 *
 * 注意：Rust reqwest不支持在HTTPS CONNECT阶段添加自定义头，
 * 因此HTTPS Proxy-Tunnel场景无法生效，仅作演示
 */

use anyhow::{anyhow, Context, Result};
use regex::Regex;
use reqwest::{header, Proxy};
use std::env;
use std::time::Duration;
use tokio::time::sleep;

// 代理配置信息
struct ProxyConfig {
    host: String,
    port: String,
    user: String,
    pass: String,
    tunnel: String,
}

impl ProxyConfig {
    fn from_env() -> Result<Self> {
        let host = getenv("PROXY_HOST", Some("t.16yun.cn"));
        let port = getenv("PROXY_PORT", Some("31111"));
        let user = getenv("PROXY_USERNAME", None).or_else(|| getenv("PROXY_USER", None));
        let pass = getenv("PROXY_PASSWORD", None).or_else(|| getenv("PROXY_PASS", None));
        let tunnel = getenv("PROXY_TUNNEL", Some("rust-reqwest-demo-12345"));

        let user = user.ok_or_else(|| anyhow!("Missing PROXY_USERNAME or PROXY_USER"))?;
        let pass = pass.ok_or_else(|| anyhow!("Missing PROXY_PASSWORD or PROXY_PASS"))?;

        if user.is_empty() || pass.is_empty() {
            return Err(anyhow!("Empty PROXY_USERNAME/PROXY_PASSWORD"));
        }

        Ok(ProxyConfig {
            host: host.unwrap_or_else(|| "t.16yun.cn".to_string()),
            port: port.unwrap_or_else(|| "31111".to_string()),
            user,
            pass,
            tunnel: tunnel.unwrap_or_else(|| "rust-reqwest-demo-12345".to_string()),
        })
    }

    fn proxy_url(&self) -> String {
        format!("http://{}:{}@{}:{}", self.user, self.pass, self.host, self.port)
    }
}

// 目标URL配置
const HTTP_TARGET_URL: &str = "http://httpbin.org/ip";

fn getenv(key: &str, default: Option<&str>) -> Option<String> {
    env::var(key)
        .ok()
        .filter(|s| !s.is_empty())
        .or_else(|| default.map(|s| s.to_string()))
}

#[tokio::main]
async fn main() -> Result<()> {
    let config = ProxyConfig::from_env()?;
    let https_target_url = getenv("TARGET_URL", Some("https://httpbin.org/ip"))
        .unwrap_or_else(|| "https://httpbin.org/ip".to_string());

    println!("=== Rust reqwest 隧道代理四种场景演示 ===");
    println!("代理服务器: {}:{}", config.host, config.port);
    println!("代理用户: {}", config.user);
    println!("Proxy-Tunnel: {}", config.tunnel);
    println!();

    // 场景A：强制新建连接（每次不同IP）
    println!("【场景A】强制新建连接 - 每次请求建立新连接获得不同IP");
    if let Err(e) = scenario_a_force_new_connection(&config, &https_target_url).await {
        eprintln!("场景A执行失败: {}", e);
    }
    println!();

    // 场景B：Keep-Alive会话保持（相同IP）
    println!("【场景B】Keep-Alive会话保持 - 复用TCP连接保持相同IP");
    if let Err(e) = scenario_b_keep_alive(&config, &https_target_url).await {
        eprintln!("场景B执行失败: {}", e);
    }
    println!();

    // 场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标）
    println!("【场景C-HTTP】Proxy-Tunnel固定IP - HTTP目标");
    if let Err(e) = scenario_c_proxy_tunnel_http(&config).await {
        eprintln!("场景C-HTTP执行失败: {}", e);
    }
    println!();

    // 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标，不支持）
    println!("【场景C-HTTPS】Proxy-Tunnel固定IP - HTTPS目标（不支持CONNECT自定义头）");
    if let Err(e) = scenario_c_proxy_tunnel_https(&config, &https_target_url).await {
        eprintln!("场景C-HTTPS执行失败: {}", e);
    }
    println!();

    println!("=== 所有场景演示完成 ===");
    Ok(())
}

/**
 * 场景A：强制新建连接
 * 每次请求建立新的TCP连接，关闭连接复用
 * 这样可以获得不同的出口IP地址
 */
async fn scenario_a_force_new_connection(config: &ProxyConfig, target_url: &str) -> Result<()> {
    println!("技术原理：每次创建新reqwest Client，关闭池化连接，添加Connection: close头");

    for i in 1..=3 {
        // 每次创建新的reqwest Client，避免连接复用
        let client = create_proxy_client(config, true)?;

        let response = client
            .get(target_url)
            .header("Connection", "close")
            .header("Proxy-Connection", "close")
            .send()
            .await
            .context("request failed")?;

        let status = response.status();
        let content = response.text().await.unwrap_or_default();
        let ip = extract_ip(&content);

        println!("请求 {}: {} - {}", i, status, ip);

        // 短暂延迟确保连接完全关闭
        sleep(Duration::from_millis(500)).await;
    }

    Ok(())
}

/**
 * 场景B：Keep-Alive会话保持
 * 复用同一个reqwest Client实例，保持TCP连接
 * 在代理会话有效期内保持相同的出口IP
 */
async fn scenario_b_keep_alive(config: &ProxyConfig, target_url: &str) -> Result<()> {
    println!("技术原理：复用同一reqwest Client实例，保持TCP连接和Keep-Alive");

    // 复用同一个reqwest Client实例
    let client = create_proxy_client(config, false)?;

    for i in 1..=3 {
        let response = client
            .get(target_url)
            .header("Connection", "keep-alive")
            .header("Proxy-Connection", "keep-alive")
            .send()
            .await
            .context("request failed")?;

        let status = response.status();
        let content = response.text().await.unwrap_or_default();
        let ip = extract_ip(&content);

        println!("请求 {}: {} - {}", i, status, ip);

        // 短暂延迟但保持连接
        sleep(Duration::from_millis(200)).await;
    }

    Ok(())
}

/**
 * 场景C：Proxy-Tunnel固定IP（HTTP目标）
 * 使用Proxy-Tunnel头标识固定会话
 * 相同Proxy-Tunnel值在有效期内使用相同出口IP
 */
async fn scenario_c_proxy_tunnel_http(config: &ProxyConfig) -> Result<()> {
    println!("技术原理：在HTTP请求头中添加Proxy-Tunnel标识");
    println!("Proxy-Tunnel值: {}", config.tunnel);

    let client = create_proxy_client(config, false)?;

    for i in 1..=3 {
        let response = client
            .get(HTTP_TARGET_URL)
            .header("Proxy-Tunnel", &config.tunnel) // 关键：添加Proxy-Tunnel头（仅对HTTP目标有效）
            .header("Connection", "keep-alive")
            .header("Proxy-Connection", "keep-alive")
            .send()
            .await
            .context("request failed")?;

        let status = response.status();
        let content = response.text().await.unwrap_or_default();
        let ip = extract_ip(&content);

        println!("请求 {}: {} - {}", i, status, ip);

        sleep(Duration::from_millis(200)).await;
    }

    Ok(())
}

/**
 * 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标）
 * 注意：Rust reqwest不支持在CONNECT阶段添加自定义头
 * 因此Proxy-Tunnel对HTTPS目标无效，这里仅作演示
 */
async fn scenario_c_proxy_tunnel_https(config: &ProxyConfig, target_url: &str) -> Result<()> {
    println!("技术原理：尝试在HTTPS请求中使用Proxy-Tunnel（注意：不会生效）");
    println!("⚠️  警告：Rust reqwest不支持CONNECT阶段自定义头，Proxy-Tunnel对HTTPS无效");
    println!("Proxy-Tunnel值: {}", config.tunnel);

    let client = create_proxy_client(config, false)?;

    for i in 1..=3 {
        let response = client
            .get(target_url)
            .header("Proxy-Tunnel", &config.tunnel) // 注意：这个头不会在CONNECT阶段发送
            .header("Connection", "keep-alive")
            .header("Proxy-Connection", "keep-alive")
            .send()
            .await
            .context("request failed")?;

        let status = response.status();
        let content = response.text().await.unwrap_or_default();
        let ip = extract_ip(&content);

        println!("请求 {}: {} - {} （Proxy-Tunnel未生效）", i, status, ip);

        sleep(Duration::from_millis(200)).await;
    }

    println!("💡 建议：如需HTTPS Proxy-Tunnel，请使用支持的语言如Go、Python或Node.js");
    Ok(())
}

/**
 * 创建代理客户端
 * @param config 代理配置
 * @param force_new_connection 是否强制每次新建连接
 */
fn create_proxy_client(config: &ProxyConfig, force_new_connection: bool) -> Result<reqwest::Client> {
    let proxy = Proxy::all(&config.proxy_url()).context("build proxy")?;

    let mut builder = reqwest::Client::builder()
        .proxy(proxy)
        .timeout(Duration::from_secs(15));

    if force_new_connection {
        // 禁用连接池，强制每次新建连接
        builder = builder.pool_max_idle_per_host(0);
    } else {
        // 标准连接池，支持连接复用
        builder = builder.pool_max_idle_per_host(5);
    }

    builder.build().context("build client")
}

/**
 * 从响应内容中提取IP地址
 */
fn extract_ip(content: &str) -> String {
    // 使用正则表达式提取IP，适用于httpbin.org/ip的JSON响应
    let re = Regex::new(r#""origin":\s*"([^"]+)""#).unwrap();
    if let Some(captures) = re.captures(content) {
        if let Some(ip_match) = captures.get(1) {
            return ip_match.as_str().to_string();
        }
    }
    "未知IP".to_string()
}

