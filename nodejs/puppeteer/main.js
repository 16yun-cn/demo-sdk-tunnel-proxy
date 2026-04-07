const puppeteer = require('puppeteer');

const host = process.env.PROXY_HOST || 't.16yun.cn';
const port = process.env.PROXY_PORT || '31111';
const user = process.env.PROXY_USERNAME || 'user';
const pass = process.env.PROXY_PASSWORD || 'password';
const target = process.env.TARGET_URL || 'http://httpbin.org/ip';

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: [
      `--proxy-server=http://${host}:${port}`,
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--ignore-certificate-errors',
      '--disable-web-security'
    ],
    ignoreHTTPSErrors: true
  });
  const page = await browser.newPage();
  await page.authenticate({ username: user, password: pass });

  const resp = await page.goto(target, { waitUntil: 'domcontentloaded', timeout: 30000 });
  const text = await page.evaluate(() => document.body.innerText);
  console.log(resp.status(), text);
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
