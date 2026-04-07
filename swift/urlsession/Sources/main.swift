import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
#if os(Linux)
import Glibc
#else
import Darwin
#endif

// 代理配置信息
struct ProxyConfig {
    let host: String
    let port: Int
    let user: String
    let pass: String
    let tunnel: String
    
    var proxyURL: URL? {
        return URL(string: "http://\(user):\(pass)@\(host):\(port)")
    }
    
    static func fromEnv() -> ProxyConfig {
        let host = ProcessInfo.processInfo.environment["PROXY_HOST"] ?? "t.16yun.cn"
        let port = Int(ProcessInfo.processInfo.environment["PROXY_PORT"] ?? "31111") ?? 31111
        let user = ProcessInfo.processInfo.environment["PROXY_USERNAME"] 
            ?? ProcessInfo.processInfo.environment["PROXY_USER"] ?? "user"
        let pass = ProcessInfo.processInfo.environment["PROXY_PASSWORD"]
            ?? ProcessInfo.processInfo.environment["PROXY_PASS"] ?? "password"
        let tunnel = ProcessInfo.processInfo.environment["PROXY_TUNNEL"] ?? "swift-urlsession-demo-12345"
        
        return ProxyConfig(host: host, port: port, user: user, pass: pass, tunnel: tunnel)
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
    let outputFile = "/tmp/swift-urlsession-curl-\(UUID().uuidString).out"
    let errorFile = "/tmp/swift-urlsession-curl-\(UUID().uuidString).err"

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

// 创建代理配置的URLSession
func createProxySession(config: ProxyConfig) -> URLSession {
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
    return URLSession(configuration: sessionConfig)
}

func runCurlScenario(
    title: String,
    description: String,
    config: ProxyConfig,
    requests: Int,
    delay: TimeInterval,
    headers: [String: String]
) {
    print("\n=== \(title) ===")
    print(description)

    let targetURL = ProcessInfo.processInfo.environment["TARGET_URL"] ?? "http://httpbin.org/ip"

    for i in 1...requests {
        if let (status, data) = runCurlRequest(url: targetURL, config: config, headers: headers) {
            let ip = extractIP(from: data)
            print("请求 \(i): \(status) - \(ip)")
        } else {
            print("请求 \(i): 错误 - curl 请求失败")
        }
        Thread.sleep(forTimeInterval: delay)
    }
}

// 场景A：强制新建连接
func scenarioAForceNewConnection(config: ProxyConfig) {
    print("\n=== 场景A：强制新建连接（强制IP切换） ===")
    print("技术原理：每次请求创建新的URLSession实例")
    print("适用场合：需要每个请求都使用不同IP的场景")
    
#if os(Linux)
    runCurlScenario(
        title: "场景A：强制新建连接（强制IP切换）",
        description: "技术原理：每次请求创建新的代理连接",
        config: config,
        requests: 3,
        delay: 0.5,
        headers: [
            "Connection": "close",
            "Proxy-Connection": "close",
        ]
    )
#else
    let targetURL = URL(string: ProcessInfo.processInfo.environment["TARGET_URL"] ?? "http://httpbin.org/ip")!
    let semaphore = DispatchSemaphore(value: 0)
    
    for i in 1...3 {
        let session = createProxySession(config: config)
        var request = URLRequest(url: targetURL)
        request.setValue("close", forHTTPHeaderField: "Connection")
        request.setValue("close", forHTTPHeaderField: "Proxy-Connection")
        
        let task = session.dataTask(with: request) { data, response, error in
            defer { semaphore.signal() }
            
            if let error = error {
                print("请求 \(i): 错误 - \(error.localizedDescription)")
                return
            }
            
            guard let httpResponse = response as? HTTPURLResponse,
                  let data = data else {
                print("请求 \(i): 无效响应")
                return
            }
            
            let ip = extractIP(from: data)
            print("请求 \(i): \(httpResponse.statusCode) - \(ip)")
        }
        
        task.resume()
        _ = semaphore.wait(timeout: .now() + 30)
        session.invalidateAndCancel()
        Thread.sleep(forTimeInterval: 0.5)
    }
#endif
}

// 场景B：Keep-Alive会话保持
func scenarioBKeepAlive(config: ProxyConfig) {
    print("\n=== 场景B：Keep-Alive会话保持（相同IP） ===")
    print("技术原理：使用同一个URLSession实例")
    print("适用场合：需要在会话期间保持相同IP的场景")
    
#if os(Linux)
    runCurlScenario(
        title: "场景B：Keep-Alive会话保持（相同IP）",
        description: "技术原理：复用同一个代理会话",
        config: config,
        requests: 3,
        delay: 0.2,
        headers: [
            "Connection": "keep-alive",
            "Proxy-Connection": "keep-alive",
        ]
    )
#else
    let targetURL = URL(string: ProcessInfo.processInfo.environment["TARGET_URL"] ?? "http://httpbin.org/ip")!
    let session = createProxySession(config: config)
    let semaphore = DispatchSemaphore(value: 0)
    
    for i in 1...3 {
        var request = URLRequest(url: targetURL)
        request.setValue("keep-alive", forHTTPHeaderField: "Connection")
        request.setValue("keep-alive", forHTTPHeaderField: "Proxy-Connection")
        
        let task = session.dataTask(with: request) { data, response, error in
            defer { semaphore.signal() }
            
            if let error = error {
                print("请求 \(i): 错误 - \(error.localizedDescription)")
                return
            }
            
            guard let httpResponse = response as? HTTPURLResponse,
                  let data = data else {
                print("请求 \(i): 无效响应")
                return
            }
            
            let ip = extractIP(from: data)
            print("请求 \(i): \(httpResponse.statusCode) - \(ip)")
        }
        
        task.resume()
        _ = semaphore.wait(timeout: .now() + 30)
        Thread.sleep(forTimeInterval: 0.2)
    }
    
    session.invalidateAndCancel()
#endif
}

// 场景C：Proxy-Tunnel固定IP（HTTP目标）
func scenarioCProxyTunnelHttp(config: ProxyConfig) {
    print("\n=== 场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标） ===")
    print("技术原理：在HTTP请求头中添加Proxy-Tunnel标识")
    print("Proxy-Tunnel值: \(config.tunnel)")
    
    let targetURL = ProcessInfo.processInfo.environment["TARGET_URL"] ?? "http://httpbin.org/ip"

#if os(Linux)
    runCurlScenario(
        title: "场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标）",
        description: "技术原理：在HTTP请求头中添加Proxy-Tunnel标识",
        config: config,
        requests: 3,
        delay: 0.2,
        headers: [
            "Connection": "keep-alive",
            "Proxy-Connection": "keep-alive",
            "Proxy-Tunnel": config.tunnel,
        ]
    )
#else
    let targetURLObject = URL(string: targetURL)!
    let session = createProxySession(config: config)
    let semaphore = DispatchSemaphore(value: 0)
    
    for i in 1...3 {
        var request = URLRequest(url: targetURLObject)
        request.setValue(config.tunnel, forHTTPHeaderField: "Proxy-Tunnel")
        request.setValue("keep-alive", forHTTPHeaderField: "Connection")
        request.setValue("keep-alive", forHTTPHeaderField: "Proxy-Connection")
        
        let task = session.dataTask(with: request) { data, response, error in
            defer { semaphore.signal() }
            
            if let error = error {
                print("请求 \(i): 错误 - \(error.localizedDescription)")
                return
            }
            
            guard let httpResponse = response as? HTTPURLResponse,
                  let data = data else {
                print("请求 \(i): 无效响应")
                return
            }
            
            let ip = extractIP(from: data)
            print("请求 \(i): \(httpResponse.statusCode) - \(ip)")
        }
        
        task.resume()
        _ = semaphore.wait(timeout: .now() + 30)
        Thread.sleep(forTimeInterval: 0.2)
    }
    
    session.invalidateAndCancel()
#endif
}

// 主函数
func main() {
    print("=== Swift URLSession 隧道代理演示 ===")
    print("⚠️  注意: URLSession 不支持 HTTPS CONNECT 自定义头")
    
    let config = ProxyConfig.fromEnv()
    
    print("代理服务器: \(config.host):\(config.port)")
    print("代理用户: \(config.user)")
    print("Proxy-Tunnel: \(config.tunnel)")
    
    scenarioAForceNewConnection(config: config)
    scenarioBKeepAlive(config: config)
    scenarioCProxyTunnelHttp(config: config)
    
    print("\n=== 所有场景演示完成 ===")
}

// 运行主函数
main()
