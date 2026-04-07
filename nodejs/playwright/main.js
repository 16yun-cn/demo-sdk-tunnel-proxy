// 16YUN(亿牛云) Node.js Playwright 隧道代理 Demo
// 环境变量：
//   PROXY_HOST/PROXY_PORT/PROXY_USERNAME/PROXY_PASSWORD
//   TARGET_URL（默认 https://httpbin.org/ip）
//   TUNNEL_SEED（可选，用于 Proxy-Tunnel 会话保持/切换）

import { chromium /*, firefox, webkit */ } from 'playwright';

const host = process.env.PROXY_HOST || 't.16yun.cn';
const port = process.env.PROXY_PORT || '31111';
const user = process.env.PROXY_USERNAME || 'user';
const pass = process.env.PROXY_PASSWORD || 'password';
const target = process.env.TARGET_URL || 'http://httpbin.org/ip';

async function main() {
  const browser = await chromium.launch({
    headless: true,
    proxy: {
      server: `http://${host}:${port}`,
      username: user,
      password: pass,
    },
  });

  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
  });
  const page = await context.newPage();

  page.on('request', (req) => console.log('>>', req.method(), req.url()));
  page.on('response', (res) => console.log('<<', res.status(), res.url()));

  await page.goto(target, { waitUntil: 'load', timeout: 60_000 });
  const content = await page.content();
  console.log(content);

  await browser.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
