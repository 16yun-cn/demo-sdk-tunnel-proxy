// 16YUN(亿牛云) Node.js axios 隧道代理演示
//
// 本示例演示四种隧道代理使用场景：
// - 场景A：每次新建连接（强制IP切换）
// - 场景B：Keep-Alive会话保持（相同IP）
// - 场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标）
// - 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标）✅支持
//
// 技术特点：
// - Node.js通过https-proxy-agent支持在CONNECT阶段添加Proxy-Tunnel头
// - 完整的四种场景实现，覆盖所有代理使用模式
// - 详细的中文注释和技术原理说明

const axios = require('axios');
const { HttpProxyAgent } = require('http-proxy-agent');
const { HttpsProxyAgent } = require('https-proxy-agent');
const { URL } = require('url');

// 获取环境变量，支持别名映射
function getEnv(name, defaultValue = '') {
  return process.env[name] || defaultValue;
}

// 构建代理认证信息，支持别名
function buildProxyAuth() {
  const user = getEnv('PROXY_USERNAME') || getEnv('PROXY_USER', 'user');
  const pass = getEnv('PROXY_PASSWORD') || getEnv('PROXY_PASS', 'password');
  return { user, pass };
}

// 构建代理URL
function buildProxyUrl() {
  const host = getEnv('PROXY_HOST', 't.16yun.cn');
  const port = getEnv('PROXY_PORT', '31111');
  const { user, pass } = buildProxyAuth();
  return `http://${user}:${pass}@${host}:${port}`;
}

// 从响应中提取IP地址
function extractIP(responseData) {
  if (typeof responseData === 'object' && responseData.origin) {
    return responseData.origin;
  }
  return '未知IP';
}

// 场景A：每次新建连接（强制IP切换）
//
// 技术原理：每次请求创建新的Agent实例，不复用连接，强制断开连接
// 适用场合：需要每个请求都使用不同IP的场景
async function scenarioAForceNewConnection() {
  console.log('\n=== 场景A：每次新建连接（强制IP切换） ===');
  console.log('技术原理：每次请求创建新的Agent实例，不复用连接，强制断开连接');
  console.log('适用场合：需要每个请求都使用不同IP的场景');

  const proxyUrl = buildProxyUrl();
  const targetUrl = getEnv('TARGET_URL', 'https://httpbin.org/ip');

  for (let i = 1; i <= 2; i++) {
    try {
      // 每次创建新的Agent实例
      const httpAgent = new HttpProxyAgent(proxyUrl);
      const httpsAgent = new HttpsProxyAgent(proxyUrl);

      const response = await axios.get(targetUrl, {
        httpAgent,
        httpsAgent,
        timeout: 15000,
        headers: {
          'Connection': 'close',
          'Proxy-Connection': 'close'
        }
      });

      if (response.status === 200) {
        const ip = extractIP(response.data);
        console.log(`请求 ${i} - IP: ${ip}`);
      } else {
        console.log(`请求 ${i} 失败 - 状态码: ${response.status}`);
      }
    } catch (error) {
      console.log(`请求 ${i} 失败: ${error.message}`);
    }
  }
}

// 场景B：Keep-Alive会话保持（相同IP）
//
// 技术原理：复用同一个Agent实例，保持TCP连接，在代理有效期内使用相同IP
// 适用场合：需要多个请求保持相同IP的场景，如登录流程
async function scenarioBKeepAlive() {
  console.log('\n=== 场景B：Keep-Alive会话保持（相同IP） ===');
  console.log('技术原理：复用同一个Agent实例，保持TCP连接，在代理有效期内使用相同IP');
  console.log('适用场合：需要多个请求保持相同IP的场景，如登录流程');

  const proxyUrl = buildProxyUrl();
  const targetUrl = getEnv('TARGET_URL', 'https://httpbin.org/ip');

  // 创建持久的Agent实例
  const httpAgent = new HttpProxyAgent(proxyUrl);
  const httpsAgent = new HttpsProxyAgent(proxyUrl);

  for (let i = 1; i <= 2; i++) {
    try {
      const response = await axios.get(targetUrl, {
        httpAgent,  // 复用同一个Agent
        httpsAgent, // 复用同一个Agent
        timeout: 15000,
        headers: {
          'Connection': 'keep-alive',
          'Proxy-Connection': 'keep-alive'
        }
      });

      if (response.status === 200) {
        const ip = extractIP(response.data);
        console.log(`请求 ${i} - IP: ${ip}`);
      } else {
        console.log(`请求 ${i} 失败 - 状态码: ${response.status}`);
      }
    } catch (error) {
      console.log(`请求 ${i} 失败: ${error.message}`);
    }
  }
}

// 场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标）
//
// 技术原理：在HTTP请求头中添加Proxy-Tunnel，相同值保持相同IP
// 适用场合：需要自定义控制IP切换的HTTP访问场景
async function scenarioCProxyTunnelHttp() {
  console.log('\n=== 场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标） ===');
  console.log('技术原理：在HTTP请求头中添加Proxy-Tunnel，相同值保持相同IP');
  console.log('适用场合：需要自定义控制IP切换的HTTP访问场景');

  const proxyUrl = buildProxyUrl();
  let tunnelValue = getEnv('PROXY_TUNNEL');

  // 如果没有设置PROXY_TUNNEL，生成一个随机值
  if (!tunnelValue) {
    tunnelValue = String(Math.floor(Math.random() * 10000) + 1);
  }

  console.log(`使用Proxy-Tunnel值: ${tunnelValue}`);

  const httpAgent = new HttpProxyAgent(proxyUrl);
  const httpsAgent = new HttpsProxyAgent(proxyUrl);

  for (let i = 1; i <= 2; i++) {
    try {
      const response = await axios.get('http://httpbin.org/ip', { // HTTP目标
        httpAgent,
        httpsAgent,
        timeout: 15000,
        headers: {
          'Proxy-Tunnel': tunnelValue,
          'Connection': 'keep-alive'
        }
      });

      if (response.status === 200) {
        const ip = extractIP(response.data);
        console.log(`请求 ${i} - IP: ${ip}`);
      } else {
        console.log(`请求 ${i} 失败 - 状态码: ${response.status}`);
      }
    } catch (error) {
      console.log(`请求 ${i} 失败: ${error.message}`);
    }
  }
}

// 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标）
//
// 技术原理：Node.js通过https-proxy-agent在CONNECT阶段携带Proxy-Tunnel头
// 适用场合：需要自定义控制IP切换的HTTPS访问场景
async function scenarioCProxyTunnelHttps() {
  console.log('\n=== 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标） ===');
  console.log('技术原理：Node.js通过https-proxy-agent在CONNECT阶段携带Proxy-Tunnel头');
  console.log('适用场合：需要自定义控制IP切换的HTTPS访问场景');

  const proxyUrl = buildProxyUrl();
  let tunnelValue = getEnv('PROXY_TUNNEL');

  // 如果没有设置PROXY_TUNNEL，生成一个随机值
  if (!tunnelValue) {
    tunnelValue = String(Math.floor(Math.random() * 10000) + 1);
  }

  console.log(`使用Proxy-Tunnel值: ${tunnelValue}`);

  // 通过 https-proxy-agent 的第二个 options 参数，把 Proxy-Tunnel 放到 CONNECT 阶段。
  const httpAgent = new HttpProxyAgent(proxyUrl);
  const httpsAgent = new HttpsProxyAgent(proxyUrl, {
    headers: {
      'Proxy-Tunnel': tunnelValue
    }
  });

  for (let i = 1; i <= 2; i++) {
    try {
      const response = await axios.get('https://httpbin.org/ip', { // HTTPS目标
        httpAgent,
        httpsAgent,
        timeout: 15000
      });

      if (response.status === 200) {
        const ip = extractIP(response.data);
        console.log(`请求 ${i} - IP: ${ip}`);
      } else {
        console.log(`请求 ${i} 失败 - 状态码: ${response.status}`);
      }
    } catch (error) {
      console.log(`请求 ${i} 失败: ${error.message}`);
    }
  }
}

async function main() {
  console.log('16YUN(亿牛云) Node.js axios 隧道代理演示');
  console.log('支持的环境变量：');
  console.log('  PROXY_HOST (默认: t.16yun.cn)');
  console.log('  PROXY_PORT (默认: 31111)');
  console.log('  PROXY_USERNAME / PROXY_USER (默认: user)');
  console.log('  PROXY_PASSWORD / PROXY_PASS (默认: password)');
  console.log('  PROXY_TUNNEL (可选: 自定义tunnel值)');
  console.log('  TARGET_URL (默认: https://httpbin.org/ip)');

  try {
    // 执行四种场景演示
    await scenarioAForceNewConnection();
    await scenarioBKeepAlive();
    await scenarioCProxyTunnelHttp();
    await scenarioCProxyTunnelHttps();

    console.log('\n演示完成！');
    console.log('注意：Node.js通过https-proxy-agent支持HTTPS下的Proxy-Tunnel');
  } catch (error) {
    console.error('演示过程中发生错误:', error.message);
    process.exit(1);
  }
}

// 运行主函数
main().catch((err) => {
  console.error('程序运行错误:', err.message);
  process.exit(1);
});
