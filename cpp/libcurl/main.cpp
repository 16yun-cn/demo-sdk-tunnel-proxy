#include <curl/curl.h>
#include <cstdlib>
#include <iostream>
#include <string>
#include <sstream>
#include <random>
#include <cstring>

// 回调函数用于处理响应数据
static size_t write_callback(char* ptr, size_t size, size_t nmemb, std::string* data) {
    data->append(ptr, size * nmemb);
    return size * nmemb;
}

// 获取环境变量的辅助函数
static const char* getEnv(const char* key, const char* defaultValue) {
    const char* value = std::getenv(key);
    return value ? value : defaultValue;
}

// 从响应中提取IP地址
std::string extractIP(const std::string& response) {
    // 简单的JSON解析，查找"origin"字段
    size_t pos = response.find("\"origin\":");
    if (pos != std::string::npos) {
        pos = response.find("\"", pos + 9);
        if (pos != std::string::npos) {
            size_t end = response.find("\"", pos + 1);
            if (end != std::string::npos) {
                return response.substr(pos + 1, end - pos - 1);
            }
        }
    }
    return "未知IP";
}

// 场景A：每次新建连接（强制IP切换）
void scenario_a_force_new_connection() {
    std::cout << "\n=== 场景A：每次新建连接（强制IP切换） ===" << std::endl;
    std::cout << "技术原理：每次请求创建新的CURL实例，添加Connection: close头，强制断开连接" << std::endl;
    std::cout << "适用场合：需要每个请求都使用不同IP的场景" << std::endl;
    
    const char* host = getEnv("PROXY_HOST", "t.16yun.cn");
    const char* port = getEnv("PROXY_PORT", "31111");
    const char* user = getEnv("PROXY_USERNAME", "user");
    const char* pass = getEnv("PROXY_PASSWORD", "password");
    const char* target = getEnv("TARGET_URL", "https://httpbin.org/ip");
    
    for (int i = 1; i <= 2; i++) {
        CURL* curl = curl_easy_init();
        if (!curl) continue;
        
        std::string response;
        struct curl_slist* headers = nullptr;
        
        // 添加强制关闭连接的头
        headers = curl_slist_append(headers, "Connection: close");
        headers = curl_slist_append(headers, "Proxy-Connection: close");
        
        // 设置代理
        std::string proxy_url = std::string("http://") + host + ":" + port;
        std::string proxy_auth = std::string(user) + ":" + pass;
        
        curl_easy_setopt(curl, CURLOPT_URL, target);
        curl_easy_setopt(curl, CURLOPT_PROXY, proxy_url.c_str());
        curl_easy_setopt(curl, CURLOPT_PROXYUSERPWD, proxy_auth.c_str());
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
        curl_easy_setopt(curl, CURLOPT_TIMEOUT, 15L);
        curl_easy_setopt(curl, CURLOPT_FRESH_CONNECT, 1L); // 强制新连接
        curl_easy_setopt(curl, CURLOPT_FORBID_REUSE, 1L);  // 禁止连接复用
        
        CURLcode res = curl_easy_perform(curl);
        if (res == CURLE_OK) {
            std::string ip = extractIP(response);
            std::cout << "请求 " << i << " - IP: " << ip << std::endl;
        } else {
            std::cerr << "请求 " << i << " 失败: " << curl_easy_strerror(res) << std::endl;
        }
        
        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);
    }
}

// 场景B：Keep-Alive会话保持（相同IP）
void scenario_b_keep_alive() {
    std::cout << "\n=== 场景B：Keep-Alive会话保持（相同IP） ===" << std::endl;
    std::cout << "技术原理：复用同一个CURL实例，保持TCP连接，在代理有效期内使用相同IP" << std::endl;
    std::cout << "适用场合：需要多个请求保持相同IP的场景，如登录流程" << std::endl;
    
    const char* host = getEnv("PROXY_HOST", "t.16yun.cn");
    const char* port = getEnv("PROXY_PORT", "31111");
    const char* user = getEnv("PROXY_USERNAME", "user");
    const char* pass = getEnv("PROXY_PASSWORD", "password");
    const char* target = getEnv("TARGET_URL", "https://httpbin.org/ip");
    
    CURL* curl = curl_easy_init();
    if (!curl) return;
    
    struct curl_slist* headers = nullptr;
    
    // 添加Keep-Alive头
    headers = curl_slist_append(headers, "Connection: keep-alive");
    headers = curl_slist_append(headers, "Proxy-Connection: keep-alive");
    
    // 设置代理
    std::string proxy_url = std::string("http://") + host + ":" + port;
    std::string proxy_auth = std::string(user) + ":" + pass;
    
    curl_easy_setopt(curl, CURLOPT_URL, target);
    curl_easy_setopt(curl, CURLOPT_PROXY, proxy_url.c_str());
    curl_easy_setopt(curl, CURLOPT_PROXYUSERPWD, proxy_auth.c_str());
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 15L);
    
    for (int i = 1; i <= 2; i++) {
        std::string response;
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
        
        CURLcode res = curl_easy_perform(curl);
        if (res == CURLE_OK) {
            std::string ip = extractIP(response);
            std::cout << "请求 " << i << " - IP: " << ip << std::endl;
        } else {
            std::cerr << "请求 " << i << " 失败: " << curl_easy_strerror(res) << std::endl;
        }
    }
    
    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);
}

// 场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标）
void scenario_c_proxy_tunnel_http() {
    std::cout << "\n=== 场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标） ===" << std::endl;
    std::cout << "技术原理：在HTTP请求头中添加Proxy-Tunnel，相同值保持相同IP" << std::endl;
    std::cout << "适用场合：需要自定义控制IP切换的HTTP访问场景" << std::endl;
    
    const char* host = getEnv("PROXY_HOST", "t.16yun.cn");
    const char* port = getEnv("PROXY_PORT", "31111");
    const char* user = getEnv("PROXY_USERNAME", "user");
    const char* pass = getEnv("PROXY_PASSWORD", "password");
    const char* tunnel_value = getEnv("PROXY_TUNNEL", "");
    
    // 如果没有设置PROXY_TUNNEL，生成一个随机值
    std::string tunnel_seed;
    if (strlen(tunnel_value) == 0) {
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_int_distribution<> dis(1, 10000);
        tunnel_seed = std::to_string(dis(gen));
    } else {
        tunnel_seed = tunnel_value;
    }
    
    std::cout << "使用Proxy-Tunnel值: " << tunnel_seed << std::endl;
    
    for (int i = 1; i <= 2; i++) {
        CURL* curl = curl_easy_init();
        if (!curl) continue;
        
        std::string response;
        struct curl_slist* headers = nullptr;
        
        // 添加Proxy-Tunnel头到HTTP请求
        std::string tunnel_header = "Proxy-Tunnel: " + tunnel_seed;
        headers = curl_slist_append(headers, tunnel_header.c_str());
        headers = curl_slist_append(headers, "Connection: keep-alive");
        
        // 设置代理
        std::string proxy_url = std::string("http://") + host + ":" + port;
        std::string proxy_auth = std::string(user) + ":" + pass;
        
        curl_easy_setopt(curl, CURLOPT_URL, "http://httpbin.org/ip");  // HTTP目标
        curl_easy_setopt(curl, CURLOPT_PROXY, proxy_url.c_str());
        curl_easy_setopt(curl, CURLOPT_PROXYUSERPWD, proxy_auth.c_str());
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
        curl_easy_setopt(curl, CURLOPT_TIMEOUT, 15L);
        
        CURLcode res = curl_easy_perform(curl);
        if (res == CURLE_OK) {
            std::string ip = extractIP(response);
            std::cout << "请求 " << i << " - IP: " << ip << std::endl;
        } else {
            std::cerr << "请求 " << i << " 失败: " << curl_easy_strerror(res) << std::endl;
        }
        
        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);
    }
}

// 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标）
void scenario_c_proxy_tunnel_https() {
    std::cout << "\n=== 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标） ===" << std::endl;
    std::cout << "技术原理：libcurl支持在CONNECT阶段携带Proxy-Tunnel头，实现HTTPS下的IP固定" << std::endl;
    std::cout << "适用场合：需要自定义控制IP切换的HTTPS访问场景" << std::endl;
    
    const char* host = getEnv("PROXY_HOST", "t.16yun.cn");
    const char* port = getEnv("PROXY_PORT", "31111");
    const char* user = getEnv("PROXY_USERNAME", "user");
    const char* pass = getEnv("PROXY_PASSWORD", "password");
    const char* tunnel_value = getEnv("PROXY_TUNNEL", "");
    
    // 如果没有设置PROXY_TUNNEL，生成一个随机值
    std::string tunnel_seed;
    if (strlen(tunnel_value) == 0) {
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_int_distribution<> dis(1, 10000);
        tunnel_seed = std::to_string(dis(gen));
    } else {
        tunnel_seed = tunnel_value;
    }
    
    std::cout << "使用Proxy-Tunnel值: " << tunnel_seed << std::endl;
    
    for (int i = 1; i <= 2; i++) {
        CURL* curl = curl_easy_init();
        if (!curl) continue;
        
        std::string response;
        struct curl_slist* headers = nullptr;
        struct curl_slist* proxy_headers = nullptr;
        
        // 为CONNECT请求添加Proxy-Tunnel头
        std::string tunnel_header = "Proxy-Tunnel: " + tunnel_seed;
        proxy_headers = curl_slist_append(proxy_headers, tunnel_header.c_str());
        
        // 设置代理
        std::string proxy_url = std::string("http://") + host + ":" + port;
        std::string proxy_auth = std::string(user) + ":" + pass;
        
        curl_easy_setopt(curl, CURLOPT_URL, "https://httpbin.org/ip");  // HTTPS目标
        curl_easy_setopt(curl, CURLOPT_PROXY, proxy_url.c_str());
        curl_easy_setopt(curl, CURLOPT_PROXYUSERPWD, proxy_auth.c_str());
        curl_easy_setopt(curl, CURLOPT_PROXYHEADER, proxy_headers); // 这是CONNECT阶段的头
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
        curl_easy_setopt(curl, CURLOPT_TIMEOUT, 15L);
        
        CURLcode res = curl_easy_perform(curl);
        if (res == CURLE_OK) {
            std::string ip = extractIP(response);
            std::cout << "请求 " << i << " - IP: " << ip << std::endl;
        } else {
            std::cerr << "请求 " << i << " 失败: " << curl_easy_strerror(res) << std::endl;
        }
        
        curl_slist_free_all(headers);
        curl_slist_free_all(proxy_headers);
        curl_easy_cleanup(curl);
    }
}

int main() {
    std::cout << "16YUN(亿牛云) C++ libcurl 隧道代理演示" << std::endl;
    std::cout << "支持的环境变量：" << std::endl;
    std::cout << "  PROXY_HOST (默认: t.16yun.cn)" << std::endl;
    std::cout << "  PROXY_PORT (默认: 31111)" << std::endl;
    std::cout << "  PROXY_USERNAME (默认: user)" << std::endl;
    std::cout << "  PROXY_PASSWORD (默认: password)" << std::endl;
    std::cout << "  PROXY_TUNNEL (可选: 自定义tunnel值)" << std::endl;
    std::cout << "  TARGET_URL (默认: https://httpbin.org/ip)" << std::endl;
    
    // 初始化libcurl
    curl_global_init(CURL_GLOBAL_DEFAULT);
    
    // 执行四种场景演示
    scenario_a_force_new_connection();
    scenario_b_keep_alive();
    scenario_c_proxy_tunnel_http();
    scenario_c_proxy_tunnel_https();
    
    std::cout << "\n演示完成！" << std::endl;
    std::cout << "注意：libcurl原生支持HTTPS下的Proxy-Tunnel（通过CURLOPT_PROXYHEADER）" << std::endl;
    
    // 清理libcurl
    curl_global_cleanup();
    
    return 0;
}
