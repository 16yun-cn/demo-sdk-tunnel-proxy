<?php
/**
 * PHP Guzzle 隧道代理四种场景演示
 * 基于16YUN爬虫代理服务的完整实现
 * 
 * 四种场景说明：
 * A. 强制新建连接 - 每次请求建立新连接，获得不同IP
 * B. Keep-Alive会话保持 - 复用TCP连接，保持相同IP  
 * C. Proxy-Tunnel固定IP (HTTP) - 使用Proxy-Tunnel头固定IP访问HTTP目标
 * C. Proxy-Tunnel固定IP (HTTPS) - 使用Proxy-Tunnel头固定IP访问HTTPS目标
 *
 * 注意：PHP Guzzle不支持在HTTPS CONNECT阶段添加自定义头，
 * 因此HTTPS Proxy-Tunnel场景无法生效，仅作演示
 */

require __DIR__ . '/vendor/autoload.php';

use GuzzleHttp\Client;

// 代理配置信息
$PROXY_HOST = getenv('PROXY_HOST') ?: 't.16yun.cn';
$PROXY_PORT = getenv('PROXY_PORT') ?: '31111';
$PROXY_USER = getenv('PROXY_USERNAME') ?: getenv('PROXY_USER') ?: 'user';
$PROXY_PASS = getenv('PROXY_PASSWORD') ?: getenv('PROXY_PASS') ?: 'password';
$PROXY_TUNNEL = getenv('PROXY_TUNNEL') ?: 'php-guzzle-demo-12345';

// 目标URL配置
$HTTP_TARGET_URL = 'http://httpbin.org/ip';
$HTTPS_TARGET_URL = getenv('TARGET_URL') ?: 'http://httpbin.org/ip';

function main()
{
    global $PROXY_HOST, $PROXY_PORT, $PROXY_USER, $PROXY_TUNNEL;

    echo "=== PHP Guzzle 隧道代理四种场景演示 ===\n";
    echo "代理服务器: {$PROXY_HOST}:{$PROXY_PORT}\n";
    echo "代理用户: {$PROXY_USER}\n";
    echo "Proxy-Tunnel: {$PROXY_TUNNEL}\n";
    echo "\n";

    try {
        // 场景A：强制新建连接（每次不同IP）
        echo "【场景A】强制新建连接 - 每次请求建立新连接获得不同IP\n";
        scenarioAForceNewConnection();
        echo "\n";

        // 场景B：Keep-Alive会话保持（相同IP）
        echo "【场景B】Keep-Alive会话保持 - 复用TCP连接保持相同IP\n";
        scenarioBKeepAlive();
        echo "\n";

        // 场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标）
        echo "【场景C-HTTP】Proxy-Tunnel固定IP - HTTP目标\n";
        scenarioCProxyTunnelHttp();
        echo "\n";

        // 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标，不支持）
        echo "【场景C-HTTPS】Proxy-Tunnel固定IP - HTTPS目标（不支持CONNECT自定义头）\n";
        scenarioCProxyTunnelHttps();
        echo "\n";

        echo "=== 所有场景演示完成 ===\n";
    } catch (Exception $e) {
        error_log("执行错误: " . $e->getMessage());
        exit(1);
    }
}

/**
 * 场景A：强制新建连接
 * 每次请求建立新的TCP连接，关闭连接复用
 * 这样可以获得不同的出口IP地址
 */
function scenarioAForceNewConnection()
{
    global $HTTPS_TARGET_URL;

    echo "技术原理：每次创建新Guzzle Client，关闭Keep-Alive，添加Connection: close头\n";

    for ($i = 1; $i <= 3; $i++) {
        // 每次创建新的Guzzle Client，避免连接复用
        $client = createProxyClient(true);

        $options = [
            'headers' => [
                'Connection' => 'close',
                'Proxy-Connection' => 'close'
            ]
        ];

        $response = $client->get($HTTPS_TARGET_URL, $options);
        $content = (string) $response->getBody();
        $ip = extractIp($content);

        echo "请求 {$i}: " . $response->getStatusCode() . " - {$ip}\n";

        // 短暂延迟确保连接完全关闭
        usleep(500000); // 500ms
    }
}

/**
 * 场景B：Keep-Alive会话保持
 * 复用同一个Guzzle Client实例，保持TCP连接
 * 在代理会话有效期内保持相同的出口IP
 */
function scenarioBKeepAlive()
{
    global $HTTPS_TARGET_URL;

    echo "技术原理：复用同一Guzzle Client实例，保持TCP连接和Keep-Alive\n";

    // 复用同一个Guzzle Client实例
    $client = createProxyClient(false);

    for ($i = 1; $i <= 3; $i++) {
        $options = [
            'headers' => [
                'Connection' => 'keep-alive',
                'Proxy-Connection' => 'keep-alive'
            ]
        ];

        $response = $client->get($HTTPS_TARGET_URL, $options);
        $content = (string) $response->getBody();
        $ip = extractIp($content);

        echo "请求 {$i}: " . $response->getStatusCode() . " - {$ip}\n";

        // 短暂延迟但保持连接
        usleep(200000); // 200ms
    }
}

/**
 * 场景C：Proxy-Tunnel固定IP（HTTP目标）
 * 使用Proxy-Tunnel头标识固定会话
 * 相同Proxy-Tunnel值在有效期内使用相同出口IP
 */
function scenarioCProxyTunnelHttp()
{
    global $HTTP_TARGET_URL, $PROXY_TUNNEL;

    echo "技术原理：在HTTP请求头中添加Proxy-Tunnel标识\n";
    echo "Proxy-Tunnel值: {$PROXY_TUNNEL}\n";

    $client = createProxyClient(false);

    for ($i = 1; $i <= 3; $i++) {
        $options = [
            'headers' => [
                'Proxy-Tunnel' => $PROXY_TUNNEL, // 关键：添加Proxy-Tunnel头（仅对HTTP目标有效）
                'Connection' => 'keep-alive',
                'Proxy-Connection' => 'keep-alive'
            ]
        ];

        $response = $client->get($HTTP_TARGET_URL, $options);
        $content = (string) $response->getBody();
        $ip = extractIp($content);

        echo "请求 {$i}: " . $response->getStatusCode() . " - {$ip}\n";

        usleep(200000);
    }
}

/**
 * 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标）
 * 注意：PHP Guzzle不支持在CONNECT阶段添加自定义头
 * 因此Proxy-Tunnel对HTTPS目标无效，这里仅作演示
 */
function scenarioCProxyTunnelHttps()
{
    global $HTTPS_TARGET_URL, $PROXY_TUNNEL;

    echo "技术原理：尝试在HTTPS请求中使用Proxy-Tunnel（注意：不会生效）\n";
    echo "⚠️  警告：PHP Guzzle不支持CONNECT阶段自定义头，Proxy-Tunnel对HTTPS无效\n";
    echo "Proxy-Tunnel值: {$PROXY_TUNNEL}\n";

    $client = createProxyClient(false);

    for ($i = 1; $i <= 3; $i++) {
        $options = [
            'headers' => [
                'Proxy-Tunnel' => $PROXY_TUNNEL, // 注意：这个头不会在CONNECT阶段发送
                'Connection' => 'keep-alive',
                'Proxy-Connection' => 'keep-alive'
            ]
        ];

        $response = $client->get($HTTPS_TARGET_URL, $options);
        $content = (string) $response->getBody();
        $ip = extractIp($content);

        echo "请求 {$i}: " . $response->getStatusCode() . " - {$ip} （Proxy-Tunnel未生效）\n";

        usleep(200000);
    }

    echo "💡 建议：如需HTTPS Proxy-Tunnel，请使用支持的语言如Go、Python或Node.js\n";
}

/**
 * 创建代理客户端
 * @param bool $forceNewConnection 是否强制每次新建连接
 * @return Client
 */
function createProxyClient($forceNewConnection = false)
{
    global $PROXY_HOST, $PROXY_PORT, $PROXY_USER, $PROXY_PASS;

    $config = [
        'timeout' => 15.0,
        'verify' => false,  // 修复: 禁用 SSL 验证（针对自签名证书的 mock 服务器）
        'proxy' => "http://{$PROXY_USER}:{$PROXY_PASS}@{$PROXY_HOST}:{$PROXY_PORT}",
    ];

    if ($forceNewConnection) {
        // 关闭Keep-Alive，强制每次新建连接
        $config['curl'] = [
            CURLOPT_FRESH_CONNECT => true,
            CURLOPT_FORBID_REUSE => true,
            CURLOPT_SSL_VERIFYPEER => false,  // 添加: 禁用 peer 验证
            CURLOPT_SSL_VERIFYHOST => false,  // 添加: 禁用 host 验证
        ];
    }

    return new Client($config);
}

/**
 * 从响应内容中提取IP地址
 * @param string $content
 * @return string
 */
function extractIp($content)
{
    try {
        // 使用正则表达式提取IP，适用于httpbin.org/ip的JSON响应
        if (preg_match('/"origin":\s*"([^"]+)"/', $content, $matches)) {
            return $matches[1];
        }
        return "未知IP";
    } catch (Exception $e) {
        return "IP解析失败";
    }
}

// 运行主函数
main();

