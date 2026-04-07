// Node.js http 隧道代理示例（直接使用 http.request + Proxy-Authorization + Proxy-Tunnel）
import http from 'http';
import { URL } from 'url';

const target = process.env.TARGET_URL || 'http://httpbin.org/ip';
const u = new URL(target);

const host = process.env.PROXY_HOST || 't.16yun.cn';
const port = process.env.PROXY_PORT || '31111';
const user = process.env.PROXY_USERNAME || 'user';
const pass = process.env.PROXY_PASSWORD || 'password';
const seed = process.env.TUNNEL_SEED || '12345';

const auth = Buffer.from(`${user}:${pass}`).toString('base64');

const options = {
  host,
  port,
  method: 'GET',
  path: target,
  headers: {
    Host: u.hostname,
    'Proxy-Authorization': `Basic ${auth}`,
    'Proxy-Tunnel': seed,
  },
};

const req = http.request(options, (res) => {
  console.log('status:', res.statusCode);
  res.setEncoding('utf8');
  res.on('data', (chunk) => process.stdout.write(chunk));
});
req.on('error', (e) => console.error('error:', e.message));
req.end();

