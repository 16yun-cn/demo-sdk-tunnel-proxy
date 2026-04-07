#include <cpr/cpr.h>
#include <cstdlib>
#include <iostream>
#include <string>
#include <sstream>
#include <regex>
#include <thread>
#include <chrono>

// 获取环境变量的辅助函数
static const char* getEnv(const char* key, const char* defaultValue) {
    const char* value = std::getenv(key);
    return value ? value : defaultValue;
}

// 从响应中提取IP地址
std::string extractIP(const std::string& response) {
    // 修复: 正确的原始字符串语法
    std::regex pattern("\"origin\":\\s*\"([^\"]+)\"");
    std::smatch match;
    
    if (std::regex_search(response, match, pattern)) {
        return match[1].str();
    }
    return "未知IP";
}

// 构建代理URL
std::string buildProxyUrl(const char* host, const char* port, const char* user, const char* pass) {
    std::ostringstream oss;
    oss << "http://" << user << ":" << pass << "@" << host << ":" << port;
    return oss.str();
}

// 场景A：每次新建连接（强制IP切换）
void scenario_a_force_new_connection() {
    std::cout << "\n=== 场景A：每次新建连接（强制IP切换） ===" << std::endl;
    std::cout << "技术原理：每次请求创建新的cpr::Session实例，强制断开连接" << std::endl;
    std::cout << "适用场合：需要每个请求都使用不同IP的场景" << std::endl;
    
    const char* host = getEnv("PROXY_HOST", "t.16yun.cn");
    const char* port = getEnv("PROXY_PORT", "31111");
    const char* user = getEnv("PROXY_USERNAME", "user");
    const char* pass = getEnv("PROXY_PASSWORD", "password");
    const char* target = getEnv("TARGET_URL", "http://httpbin.org/ip");
    
    std::string proxyUrl = buildProxyUrl(host, port, user, pass);
    
    for (int i = 1; i <= 3; i++) {
        // 每次创建新的Session实例
        cpr::Session session;
        
        // 修复: 使用正确的代理设置方式
        session.SetProxies(cpr::Proxies{{"http", proxyUrl}, {"https", proxyUrl}});
        session.SetUrl(cpr::Url{target});
        session.SetTimeout(cpr::Timeout{15000});
        
        // 强制关闭连接
        session.SetHeader(cpr::Header{
            {"Connection", "close"},
            {"Proxy-Connection", "close"}
        });
        
        auto response = session.Get();
        
        if (response.status_code == 200) {
            std::string ip = extractIP(response.text);
            std::cout << "请求 " << i << ": " << response.status_code << " - " << ip << std::endl;
        } else {
            std::cout << "请求 " << i << ": 错误 " << response.status_code << " - " << response.error.message << std::endl;
        }
        
        std::this_thread::sleep_for(std::chrono::milliseconds(500));
    }
}

// 场景B：Keep-Alive会话保持
void scenario_b_keep_alive() {
    std::cout << "\n=== 场景B：Keep-Alive会话保持 ===" << std::endl;
    std::cout << "技术原理：使用同一个cpr::Session实例，保持TCP连接和Keep-Alive" << std::endl;
    std::cout << "适用场合：需要在会话期间保持相同IP的场景" << std::endl;
    
    const char* host = getEnv("PROXY_HOST", "t.16yun.cn");
    const char* port = getEnv("PROXY_PORT", "31111");
    const char* user = getEnv("PROXY_USERNAME", "user");
    const char* pass = getEnv("PROXY_PASSWORD", "password");
    const char* target = getEnv("TARGET_URL", "http://httpbin.org/ip");
    
    std::string proxyUrl = buildProxyUrl(host, port, user, pass);
    
    // 使用同一个Session实例进行多次请求
    cpr::Session session;
    
    session.SetProxies(cpr::Proxies{{"http", proxyUrl}, {"https", proxyUrl}});
    session.SetUrl(cpr::Url{target});
    session.SetTimeout(cpr::Timeout{15000});
    
    session.SetHeader(cpr::Header{
        {"Connection", "keep-alive"},
        {"Proxy-Connection", "keep-alive"}
    });
    
    for (int i = 1; i <= 3; i++) {
        auto response = session.Get();
        
        if (response.status_code == 200) {
            std::string ip = extractIP(response.text);
            std::cout << "请求 " << i << ": " << response.status_code << " - " << ip << std::endl;
        } else {
            std::cout << "请求 " << i << ": 错误 " << response.status_code << " - " << response.error.message << std::endl;
        }
        
        std::this_thread::sleep_for(std::chrono::milliseconds(200));
    }
}

// 场景C：Proxy-Tunnel固定IP（HTTP目标）
void scenario_c_proxy_tunnel_http() {
    std::cout << "\n=== 场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标） ===" << std::endl;
    std::cout << "技术原理：在HTTP请求头中添加Proxy-Tunnel标识" << std::endl;
    std::cout << "适用场合：需要使用固定IP访问HTTP目标的场景" << std::endl;
    
    const char* host = getEnv("PROXY_HOST", "t.16yun.cn");
    const char* port = getEnv("PROXY_PORT", "31111");
    const char* user = getEnv("PROXY_USERNAME", "user");
    const char* pass = getEnv("PROXY_PASSWORD", "password");
    const char* tunnel = getEnv("PROXY_TUNNEL", "cpp-cpr-demo-12345");
    
    std::string http_target = "http://httpbin.org/ip";
    std::string proxyUrl = buildProxyUrl(host, port, user, pass);
    
    std::cout << "Proxy-Tunnel值: " << tunnel << std::endl;
    
    cpr::Session session;
    
    session.SetProxies(cpr::Proxies{{"http", proxyUrl}, {"https", proxyUrl}});
    session.SetUrl(cpr::Url{http_target});
    session.SetTimeout(cpr::Timeout{15000});
    
    // 添加Proxy-Tunnel头（仅对HTTP目标有效）
    session.SetHeader(cpr::Header{
        {"Proxy-Tunnel", tunnel},
        {"Connection", "keep-alive"},
        {"Proxy-Connection", "keep-alive"}
    });
    
    for (int i = 1; i <= 3; i++) {
        auto response = session.Get();
        
        if (response.status_code == 200) {
            std::string ip = extractIP(response.text);
            std::cout << "请求 " << i << ": " << response.status_code << " - " << ip << std::endl;
        } else {
            std::cout << "请求 " << i << ": 错误 " << response.status_code << " - " << response.error.message << std::endl;
        }
        
        std::this_thread::sleep_for(std::chrono::milliseconds(200));
    }
}

int main() {
    std::cout << "=== C++ cpr 隧道代理演示 ===" << std::endl;
    std::cout << "⚠️  注意: cpr 不支持 HTTPS CONNECT 自定义头，仅演示 HTTP 场景" << std::endl;
    
    const char* host = getEnv("PROXY_HOST", "t.16yun.cn");
    const char* port = getEnv("PROXY_PORT", "31111");
    const char* user = getEnv("PROXY_USERNAME", "user");
    const char* tunnel = getEnv("PROXY_TUNNEL", "cpp-cpr-demo-12345");
    
    std::cout << "代理服务器: " << host << ":" << port << std::endl;
    std::cout << "代理用户: " << user << std::endl;
    std::cout << "Proxy-Tunnel: " << tunnel << std::endl;
    
    try {
        scenario_a_force_new_connection();
        scenario_b_keep_alive();
        scenario_c_proxy_tunnel_http();
        
        std::cout << "\n=== 所有场景演示完成 ===" << std::endl;
        
    } catch (const std::exception& e) {
        std::cerr << "错误: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}
