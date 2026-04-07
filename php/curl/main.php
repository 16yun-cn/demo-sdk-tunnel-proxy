<?php
// 16YUN PHP cURL 隧道示例
$host = getenv('PROXY_HOST') ?: 't.16yun.cn';
$port = getenv('PROXY_PORT') ?: '31111';
$user = getenv('PROXY_USERNAME') ?: 'user';
$pass = getenv('PROXY_PASSWORD') ?: 'password';
$target = getenv('TARGET_URL') ?: 'http://httpbin.org/ip';
$tunnel = getenv('PROXY_TUNNEL') ?: 'php-curl-demo';
$caFile = getenv('CURL_CA_BUNDLE') ?: '';

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $target);
curl_setopt($ch, CURLOPT_HEADER, 0);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
curl_setopt($ch, CURLOPT_PROXY, $host);
curl_setopt($ch, CURLOPT_PROXYPORT, intval($port));
curl_setopt($ch, CURLOPT_PROXYTYPE, CURLPROXY_HTTP);
curl_setopt($ch, CURLOPT_PROXYUSERPWD, $user . ':' . $pass);
curl_setopt($ch, CURLOPT_PROXYHEADER, ["Proxy-Tunnel: {$tunnel}"]);
if ($caFile !== '' && str_starts_with($target, 'https://')) {
  curl_setopt($ch, CURLOPT_CAINFO, $caFile);
}
$data = curl_exec($ch);
if ($data === false) {
  fwrite(STDERR, 'curl error: ' . curl_error($ch) . "\n");
}
curl_close($ch);
echo $data, "\n";
?>
