<?php
// 16YUN PHP stream wrapper 隧道示例
$host = getenv('PROXY_HOST') ?: 't.16yun.cn';
$port = getenv('PROXY_PORT') ?: '31111';
$user = getenv('PROXY_USERNAME') ?: 'user';
$pass = getenv('PROXY_PASSWORD') ?: 'password';
$seed = getenv('TUNNEL_SEED') ?: '1';
$target = getenv('TARGET_URL') ?: 'http://httpbin.org/ip';

$proxy = "tcp://{$host}:{$port}";
$auth = base64_encode("{$user}:{$pass}");
$headers = implode("\r\n", [
  "Proxy-Authorization: Basic {$auth}",
  "Proxy-Tunnel: {$seed}",
]);

$opts = [
  'http' => [
    'proxy' => $proxy,
    'header' => $headers,
    'method' => 'GET',
    'request_fulluri' => true,
    'timeout' => 15,
  ],
];

$ctx = stream_context_create($opts);
echo file_get_contents($target, false, $ctx), "\n";
?>
