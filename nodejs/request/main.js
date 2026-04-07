// Node.js 隧道代理示例（request）
import request from 'request';

const target = process.env.TARGET_URL || 'http://httpbin.org/ip';
const host = process.env.PROXY_HOST || 't.16yun.cn';
const port = process.env.PROXY_PORT || '31111';
const user = process.env.PROXY_USERNAME || 'user';
const pass = process.env.PROXY_PASSWORD || 'password';
const seed = process.env.PROXY_TUNNEL || '1';

const proxyUrl = `http://${user}:${pass}@${host}:${port}`;
const proxiedRequest = request.defaults({
  proxy: proxyUrl,
  timeout: 15000,
  headers: { 'Proxy-Tunnel': String(seed) },
  proxyHeaderExclusiveList: ['Proxy-Tunnel']
});

proxiedRequest.get({ url: target }, (err, res, body) => {
  if (err) {
    console.error(err);
    process.exit(1);
  }
  console.log('status:', res?.statusCode);
  process.stdout.write(body || '');
});
