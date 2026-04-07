// Node.js 隧道代理示例（superagent + proxy agents）
import superagent from 'superagent';
import httpProxyAgentPkg from 'http-proxy-agent';
import httpsProxyAgentPkg from 'https-proxy-agent';

const target = process.env.TARGET_URL || 'http://httpbin.org/ip';
const host = process.env.PROXY_HOST || 't.16yun.cn';
const port = process.env.PROXY_PORT || '31111';
const user = process.env.PROXY_USERNAME || 'user';
const pass = process.env.PROXY_PASSWORD || 'password';
const seed = process.env.PROXY_TUNNEL || '1';
const { HttpProxyAgent } = httpProxyAgentPkg;
const { HttpsProxyAgent } = httpsProxyAgentPkg;

const proxyUrl = `http://${user}:${pass}@${host}:${port}`;
const proxyOpts = {
  protocol: 'http:',
  host,
  hostname: host,
  port: Number(port),
  auth: `${user}:${pass}`,
  headers: { 'Proxy-Tunnel': String(seed) }
};
const agent = target.startsWith('https:')
  ? new HttpsProxyAgent(proxyOpts)
  : new HttpProxyAgent(proxyOpts);

superagent
  .get(target)
  .agent(agent)
  .set('Proxy-Tunnel', String(seed))
  .timeout({ response: 15000 })
  .then((res) => {
    console.log('status:', res.status);
    console.log(res.text);
  })
  .catch((err) => {
    console.error(err.message);
    process.exit(1);
  });
