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

async function once(i) {
  return new Promise((resolve, reject) => {
    const opts = new URL(target);
    opts.agent = agent;
    const req = https.request(opts, (res) => {
      let buf = '';
      res.setEncoding('utf8');
      res.on('data', (c) => (buf += c));
      res.on('end', () => {
        console.log(`#${i} status:`, res.statusCode);
        console.log(buf.trim());
        resolve();
      });
    });
    req.on('error', reject);
    req.end();
  });
}

(async () => {
  for (let i = 1; i <= 5; i++) {
    await once(i);
  }
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
