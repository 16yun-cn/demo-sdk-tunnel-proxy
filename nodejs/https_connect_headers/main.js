// Node.js https 隧道代理示例（https-proxy-agent + CONNECT 阶段 Proxy-Tunnel 头）
import https from 'https';
import { URL } from 'url';
import { HttpsProxyAgent } from 'https-proxy-agent';

const target = process.env.TARGET_URL || 'https://httpbin.org/ip';
const host = process.env.PROXY_HOST || 't.16yun.cn';
const port = process.env.PROXY_PORT || '31111';
const user = process.env.PROXY_USERNAME || 'user';
const pass = process.env.PROXY_PASSWORD || 'password';
const seed = process.env.TUNNEL_SEED || '1';

const proxyUrl = `http://${user}:${pass}@${host}:${port}`;
const agent = new HttpsProxyAgent(proxyUrl, {
  headers: { 'Proxy-Tunnel': String(seed) }
});

const opts = new URL(target);
opts.agent = agent;

const req = https.request(opts, (res) => {
  console.log('status:', res.statusCode);
  res.setEncoding('utf8');
  res.on('data', (chunk) => process.stdout.write(chunk));
});
req.on('error', (e) => console.error('error:', e.message));
req.end();
