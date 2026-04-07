import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
#if os(Linux)
import Glibc
#else
import Darwin
#endif
import Alamofire

// 代理配置信息
struct ProxyConfig {
    let host: String
    let port: Int
    let user: String
    let pass: String
    let tunnel: String
    
    static func fromEnv() -> ProxyConfig {
        let host = ProcessInfo.processInfo.environment["PROXY_HOST"] ?? "t.16yun.cn"
        let port = Int(ProcessInfo.processInfo.environment["PROXY_PORT"] ?? "31111") ?? 31111
        let user = ProcessInfo.processInfo.environment["PROXY_USERNAME"] 
            ?? ProcessInfo.processInfo.environment["PROXY_USER"] ?? "user"
        let pass = ProcessInfo.processInfo.environment["PROXY_PASSWORD"]
            ?? ProcessInfo.processInfo.environment["PROXY_PASS"] ?? "password"
        let tunnel = ProcessInfo.processInfo.environment["PROXY_TUNNEL"] ?? "swift-alamofire-demo-12345"
        
        return ProxyConfig(host: host, port: port, user: user, pass: pass, tunnel: tunnel)
    }
}

// 代理委托类
class ProxyDelegate: SessionDelegate {
    let config: ProxyConfig
    
    init(config: ProxyConfig) {
        self.config = config
        super.init()
    }
}

// 从响应中提取IP
func extractIP(from data: Data) -> String {
    guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
          let origin = json["origin"] as? String else {
        return "未知IP"
    }
    return origin
}

func shellEscape(_ value: String) -> String {
    "'" + value.replacingOccurrences(of: "'", with: "'\"'\"'") + "'"
}

func runCurlRequest(url: String, config: ProxyConfig, headers: [String: String]) -> (Int, Data)? {
    let outputFile = "/tmp/swift-alamofire-curl-\(UUID().uuidString).out"
    let errorFile = "/tmp/swift-alamofire-curl-\(UUID().uuidString).err"

    var commandParts = [
        "/usr/bin/curl",
        "-sS",
        "--proxy", shellEscape("http://\(config.host):\(config.port)"),
        "--proxy-user", shellEscape("\(config.user):\(config.pass)"),
        "--connect-timeout", "15",
        "--max-time", "15",
    ]
    for key in headers.keys.sorted() {
        if let value = headers[key] {
            commandParts += ["-H", shellEscape("\(key): \(value)")]
        }
    }
    commandParts += ["-w", shellEscape("\\n%{http_code}"), shellEscape(url)]

    let command = commandParts.joined(separator: " ")
        + " > " + shellEscape(outputFile)
        + " 2> " + shellEscape(errorFile)
    let status = system(command)

    defer {
        try? FileManager.default.removeItem(atPath: outputFile)
        try? FileManager.default.removeItem(atPath: errorFile)
    }

    guard status == 0 else {
        if let message = try? String(contentsOfFile: errorFile, encoding: .utf8),
           !message.isEmpty {
            print("curl 请求失败: \(message)")
        }
        return nil
    }

    guard let output = try? Data(contentsOf: URL(fileURLWithPath: outputFile)),
          let outputString = String(data: output, encoding: .utf8),
          let newlineIndex = outputString.lastIndex(of: "\n"),
          let statusCode = Int(outputString[outputString.index(after: newlineIndex)...].trimmingCharacters(in: .whitespacesAndNewlines)) else {
        return nil
    }

    let body = String(outputString[..<newlineIndex])
    return (statusCode, Data(body.utf8))
}

// 创建代理Session
func createProxySession(config: ProxyConfig) -> Session {
    let sessionConfig = URLSessionConfiguration.default
    sessionConfig.connectionProxyDictionary = [
        "HTTPEnable": 1,
        "HTTPProxy": config.host,
        "HTTPPort": config.port,
        "HTTPSEnable": 1,
        "HTTPSProxy": config.host,
        "HTTPSPort": config.port,
        "ProxyUsername": config.user,
        "ProxyPassword": config.pass
    ]
    sessionConfig.timeoutIntervalForRequest = 15.0
    
    return Session(configuration: sessionConfig)
}

// 场景A：强制新建连接
func scenarioAForceNewConnection(config: ProxyConfig) {
    print("\n=== 场景A：强制新建连接（强制IP切换） ===")
    print("技术原理：每次请求创建新的Session实例")
    
    let targetURL = ProcessInfo.processInfo.environment["TARGET_URL"] ?? "http://httpbin.org/ip"
    let semaphore = DispatchSemaphore(value: 0)
    
    for i in 1...3 {
        let session = createProxySession(config: config)
        let headers: HTTPHeaders = [
            "Connection": "close",
            "Proxy-Connection": "close"
        ]
        
        session.request(targetURL, headers: headers).responseData { response in
            defer { semaphore.signal() }
            
            switch response.result {
            case .success(let data):
                let ip = extractIP(from: data)
                print("请求 \(i): \(response.response?.statusCode ?? 0) - \(ip)")
            case .failure(let error):
                print("请求 \(i): 错误 - \(error.localizedDescription)")
            }
        }
        
        _ = semaphore.wait(timeout: .now() + 30)
        Thread.sleep(forTimeInterval: 0.5)
    }
}

// 场景B：Keep-Alive会话保持
func scenarioBKeepAlive(config: ProxyConfig) {
    print("\n=== 场景B：Keep-Alive会话保持（相同IP） ===")
    print("技术原理：使用同一个Session实例")
    
    let targetURL = ProcessInfo.processInfo.environment["TARGET_URL"] ?? "http://httpbin.org/ip"
    let session = createProxySession(config: config)
    let semaphore = DispatchSemaphore(value: 0)
    
    let headers: HTTPHeaders = [
        "Connection": "keep-alive",
        "Proxy-Connection": "keep-alive"
    ]
    
    for i in 1...3 {
        session.request(targetURL, headers: headers).responseData { response in
            defer { semaphore.signal() }
            
            switch response.result {
            case .success(let data):
                let ip = extractIP(from: data)
                print("请求 \(i): \(response.response?.statusCode ?? 0) - \(ip)")
            case .failure(let error):
                print("请求 \(i): 错误 - \(error.localizedDescription)")
            }
        }
        
        _ = semaphore.wait(timeout: .now() + 30)
        Thread.sleep(forTimeInterval: 0.2)
    }
}

// 场景C：Proxy-Tunnel固定IP
func scenarioCProxyTunnelHttp(config: ProxyConfig) {
    print("\n=== 场景C-HTTP：Proxy-Tunnel固定IP ===")
    print("Proxy-Tunnel值: \(config.tunnel)")
    
    let targetURL = ProcessInfo.processInfo.environment["TARGET_URL"] ?? "http://httpbin.org/ip"

    let headers: HTTPHeaders = [
        "Proxy-Tunnel": config.tunnel,
        "Connection": "keep-alive",
        "Proxy-Connection": "keep-alive"
    ]
    
#if os(Linux)
    for i in 1...3 {
        if let (status, data) = runCurlRequest(
            url: targetURL,
            config: config,
            headers: [
                "Connection": "keep-alive",
                "Proxy-Connection": "keep-alive",
                "Proxy-Tunnel": config.tunnel,
            ]
        ) {
            let ip = extractIP(from: data)
            print("请求 \(i): \(status) - \(ip)")
        } else {
            print("请求 \(i): 错误 - curl 请求失败")
        }
        Thread.sleep(forTimeInterval: 0.2)
    }
#else
    let session = createProxySession(config: config)
    let semaphore = DispatchSemaphore(value: 0)
    for i in 1...3 {
        session.request(targetURL, headers: headers).responseData { response in
            defer { semaphore.signal() }
            
            switch response.result {
            case .success(let data):
                let ip = extractIP(from: data)
                print("请求 \(i): \(response.response?.statusCode ?? 0) - \(ip)")
            case .failure(let error):
                print("请求 \(i): 错误 - \(error.localizedDescription)")
            }
        }
        
        _ = semaphore.wait(timeout: .now() + 30)
        Thread.sleep(forTimeInterval: 0.2)
    }
#endif
}

// 主函数
func main() {
    print("=== Swift Alamofire 隧道代理演示 ===")
    
    let config = ProxyConfig.fromEnv()
    
    print("代理服务器: \(config.host):\(config.port)")
    print("代理用户: \(config.user)")
    print("Proxy-Tunnel: \(config.tunnel)")
    
    scenarioAForceNewConnection(config: config)
    scenarioBKeepAlive(config: config)
    scenarioCProxyTunnelHttp(config: config)
    
    print("\n=== 所有场景演示完成 ===")
}

// 运行
main()
