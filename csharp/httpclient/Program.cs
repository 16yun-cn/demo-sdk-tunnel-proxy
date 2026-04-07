using System;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;

/// <summary>
/// C# HttpClient 隧道代理四种场景演示
/// 基于16YUN爬虫代理服务的完整实现
/// 
/// 四种场景说明：
/// A. 强制新建连接 - 每次请求建立新连接，获得不同IP
/// B. Keep-Alive会话保持 - 复用TCP连接，保持相同IP  
/// C. Proxy-Tunnel固定IP (HTTP) - 使用Proxy-Tunnel头固定IP访问HTTP目标
/// C. Proxy-Tunnel固定IP (HTTPS) - 使用Proxy-Tunnel头固定IP访问HTTPS目标
///
/// 注意：C# HttpClient不支持在HTTPS CONNECT阶段添加自定义头，
/// 因此HTTPS Proxy-Tunnel场景无法生效，仅作演示
/// </summary>
class Program
{
    // 代理配置信息
    private static readonly string ProxyHost = Environment.GetEnvironmentVariable("PROXY_HOST") ?? "t.16yun.cn";
    private static readonly string ProxyPort = Environment.GetEnvironmentVariable("PROXY_PORT") ?? "31111";
    private static readonly string ProxyUser = Environment.GetEnvironmentVariable("PROXY_USERNAME") ?? 
                                               Environment.GetEnvironmentVariable("PROXY_USER") ?? "user";
    private static readonly string ProxyPass = Environment.GetEnvironmentVariable("PROXY_PASSWORD") ?? 
                                               Environment.GetEnvironmentVariable("PROXY_PASS") ?? "password";
    private static readonly string ProxyTunnel = Environment.GetEnvironmentVariable("PROXY_TUNNEL") ?? "csharp-demo-12345";
    
    // 目标URL配置
    private static readonly string HttpTargetUrl = "http://httpbin.org/ip";
    private static readonly string HttpsTargetUrl = Environment.GetEnvironmentVariable("TARGET_URL") ?? "https://httpbin.org/ip";

    static async Task Main()
    {
        Console.WriteLine("=== C# HttpClient 隧道代理四种场景演示 ===");
        Console.WriteLine($"代理服务器: {ProxyHost}:{ProxyPort}");
        Console.WriteLine($"代理用户: {ProxyUser}");
        Console.WriteLine($"Proxy-Tunnel: {ProxyTunnel}");
        Console.WriteLine();

        try
        {
            // 场景A：强制新建连接（每次不同IP）
            Console.WriteLine("【场景A】强制新建连接 - 每次请求建立新连接获得不同IP");
            await ScenarioA_ForceNewConnection();
            Console.WriteLine();

            // 场景B：Keep-Alive会话保持（相同IP）
            Console.WriteLine("【场景B】Keep-Alive会话保持 - 复用TCP连接保持相同IP");
            await ScenarioB_KeepAlive();
            Console.WriteLine();

            // 场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标）
            Console.WriteLine("【场景C-HTTP】Proxy-Tunnel固定IP - HTTP目标");
            await ScenarioC_ProxyTunnelHttp();
            Console.WriteLine();

            // 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标，不支持）
            Console.WriteLine("【场景C-HTTPS】Proxy-Tunnel固定IP - HTTPS目标（不支持CONNECT自定义头）");
            await ScenarioC_ProxyTunnelHttps();
            Console.WriteLine();

            Console.WriteLine("=== 所有场景演示完成 ===");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"执行错误: {ex.Message}");
            Environment.Exit(1);
        }
    }

    /// <summary>
    /// 场景A：强制新建连接
    /// 每次请求建立新的TCP连接，关闭连接复用
    /// 这样可以获得不同的出口IP地址
    /// </summary>
    private static async Task ScenarioA_ForceNewConnection()
    {
        Console.WriteLine("技术原理：每次请求建立新TCP连接，添加Connection: close头");
        
        for (int i = 1; i <= 3; i++)
        {
            // 每次创建新的HttpClient，避免连接复用
            var handler = CreateHandler();
            
            using var client = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(15) };
            using var request = new HttpRequestMessage(HttpMethod.Get, HttpsTargetUrl);
            
            // 添加强制关闭连接的头
            request.Headers.Add("Connection", "close");
            request.Headers.Add("Proxy-Connection", "close");
            var response = await client.SendAsync(request);
            var content = await response.Content.ReadAsStringAsync();
            
            Console.WriteLine($"请求 {i}: {response.StatusCode} - {ExtractIp(content)}");
            
            // 短暂延迟确保连接完全关闭
            await Task.Delay(500);
        }
    }

    /// <summary>
    /// 场景B：Keep-Alive会话保持
    /// 复用同一个HttpClient实例，保持TCP连接
    /// 在代理会话有效期内保持相同的出口IP
    /// </summary>
    private static async Task ScenarioB_KeepAlive()
    {
        Console.WriteLine("技术原理：复用同一HttpClient实例，保持TCP连接和Keep-Alive");
        
        var handler = CreateHandler();
        
        // 复用同一个HttpClient实例
        using var client = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(15) };
        
        for (int i = 1; i <= 3; i++)
        {
            using var request = new HttpRequestMessage(HttpMethod.Get, HttpsTargetUrl);
            
            // 显式设置Keep-Alive头
            request.Headers.Add("Connection", "keep-alive");
            request.Headers.Add("Proxy-Connection", "keep-alive");
            var response = await client.SendAsync(request);
            var content = await response.Content.ReadAsStringAsync();
            
            Console.WriteLine($"请求 {i}: {response.StatusCode} - {ExtractIp(content)}");
            
            // 短暂延迟但保持连接
            await Task.Delay(200);
        }
    }

    /// <summary>
    /// 场景C：Proxy-Tunnel固定IP（HTTP目标）
    /// 使用Proxy-Tunnel头标识固定会话
    /// 相同Proxy-Tunnel值在有效期内使用相同出口IP
    /// </summary>
    private static async Task ScenarioC_ProxyTunnelHttp()
    {
        Console.WriteLine("技术原理：在HTTP请求头中添加Proxy-Tunnel标识");
        Console.WriteLine($"Proxy-Tunnel值: {ProxyTunnel}");
        
        var handler = CreateHandler();
        
        using var client = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(15) };
        
        for (int i = 1; i <= 3; i++)
        {
            using var request = new HttpRequestMessage(HttpMethod.Get, HttpTargetUrl);
            
            // 关键：添加Proxy-Tunnel头（仅对HTTP目标有效）
            request.Headers.Add("Proxy-Tunnel", ProxyTunnel);
            request.Headers.Add("Connection", "keep-alive");
            request.Headers.Add("Proxy-Connection", "keep-alive");
            var response = await client.SendAsync(request);
            var content = await response.Content.ReadAsStringAsync();
            
            Console.WriteLine($"请求 {i}: {response.StatusCode} - {ExtractIp(content)}");
            
            await Task.Delay(200);
        }
    }

    /// <summary>
    /// 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标）
    /// 注意：C# HttpClient不支持在CONNECT阶段添加自定义头
    /// 因此Proxy-Tunnel对HTTPS目标无效，这里仅作演示
    /// </summary>
    private static async Task ScenarioC_ProxyTunnelHttps()
    {
        Console.WriteLine("技术原理：尝试在HTTPS请求中使用Proxy-Tunnel（注意：不会生效）");
        Console.WriteLine("⚠️  警告：C# HttpClient不支持CONNECT阶段自定义头，Proxy-Tunnel对HTTPS无效");
        Console.WriteLine($"Proxy-Tunnel值: {ProxyTunnel}");
        
        var handler = CreateHandler();
        
        using var client = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(15) };
        
        for (int i = 1; i <= 3; i++)
        {
            using var request = new HttpRequestMessage(HttpMethod.Get, HttpsTargetUrl);
            
            // 注意：这个头不会在CONNECT阶段发送，因此对HTTPS无效
            request.Headers.Add("Proxy-Tunnel", ProxyTunnel);
            request.Headers.Add("Connection", "keep-alive");
            request.Headers.Add("Proxy-Connection", "keep-alive");
            var response = await client.SendAsync(request);
            var content = await response.Content.ReadAsStringAsync();
            
            Console.WriteLine($"请求 {i}: {response.StatusCode} - {ExtractIp(content)} （Proxy-Tunnel未生效）");
            
            await Task.Delay(200);
        }
        
        Console.WriteLine("💡 建议：如需HTTPS Proxy-Tunnel，请使用支持的语言如Go、Python或Node.js");
    }

    /// <summary>
    /// 创建代理配置
    /// </summary>
    private static NetworkCredential CreateProxyCredentials()
    {
        return new NetworkCredential(ProxyUser, ProxyPass);
    }

    private static WebProxy CreateProxy()
    {
        var encodedUser = Uri.EscapeDataString(ProxyUser);
        var encodedPass = Uri.EscapeDataString(ProxyPass);
        return new WebProxy(new Uri($"http://{encodedUser}:{encodedPass}@{ProxyHost}:{ProxyPort}"))
        {
            Credentials = CreateProxyCredentials()
        };
    }

    private static HttpClientHandler CreateHandler()
    {
        return new HttpClientHandler
        {
            Proxy = CreateProxy(),
            UseProxy = true,
            PreAuthenticate = true,
            DefaultProxyCredentials = CreateProxyCredentials(),
        };
    }

    /// <summary>
    /// 从响应内容中提取IP地址
    /// </summary>
    private static string ExtractIp(string content)
    {
        try
        {
            // 简单的IP提取，适用于httpbin.org/ip的JSON响应
            var startIndex = content.IndexOf("\"origin\":") + 10;
            if (startIndex < 10) return "未知IP";
            
            var endIndex = content.IndexOf("\"", startIndex);
            if (endIndex < 0) return "未知IP";
            
            return content.Substring(startIndex, endIndex - startIndex).Trim('"');
        }
        catch
        {
            return "IP解析失败";
        }
    }
}
