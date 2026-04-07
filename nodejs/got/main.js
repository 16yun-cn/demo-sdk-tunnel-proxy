// 16YUN(亿牛云) Node.js got 隧道代理演示
//
// 本示例演示四种隧道代理使用场景：
// - 场景A：每次新建连接（强制IP切换）
// - 场景B：Keep-Alive会话保持（相同IP）
// - 场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标）
// - 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标）✅支持
//
// 技术特点：
// - got支持通过底层Agent配置在CONNECT阶段添加Proxy-Tunnel头
// - 完整的四种场景实现，覆盖所有代理使用模式
// - 详细的中文注释和技术原理说明

import got from 'got';
import { HttpProxyAgent } from 'http-proxy-agent';
import { HttpsProxyAgent } from 'https-proxy-agent';

// 获取环境变量，支持别名映射
function getEnv(name, defaultValue = '') {
  return process.env[name] || defaultValue;
}

// 构建代理认证信息，支持别名
function buildProxyAuth() {
  const user = getEnv('PROXY_USERNAME') || getEnv('PROXY_USER', 'username');
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
// 技术原理：每次请求创建新的got实例和新的Agent，不复用连接
// 适用场合：需要每个请求都使用不同IP的场景
async function scenarioAForceNewConnection() {
  console.log('\n=== 场景A：每次新建连接（强制IP切换） ===');
  console.log('技术原理：每次请求创建新的got实例和Agent，强制断开连接');
  console.log('适用场合：需要每个请求都使用不同IP的场景');
  
  const proxyUrl = buildProxyUrl();
  const targetUrl = getEnv('TARGET_URL', 'https://httpbin.org/ip');
  
  for (let i = 1; i <= 3; i++) {
    try {
      // 每次创建新的Agent实例
      const httpsAgent = new HttpsProxyAgent(proxyUrl);
      
      // 每次创建新的got实例
      const client = got.extend({
        agent: {
          https: httpsAgent
        },
        headers: {
          'Connection': 'close',
          'Proxy-Connection': 'close'
        },
        timeout: {
          request: 15000
        },
        // 禁用HTTP/2和连接复用
        http2: false
      });
      
      const response = await client.get(targetUrl).json();
      const ip = extractIP(response);
      
      console.log(`请求 ${i}: 200 - ${ip}`);
      
      // 短暂延迟确保连接完全关闭
      await new Promise(resolve => setTimeout(resolve, 500));
    } catch (error) {
      console.log(`请求 ${i}: 错误 - ${error.message}`);
    }
  }
}

// 场景B：Keep-Alive会话保持（相同IP）
//
// 技术原理：使用同一个got实例和Agent，保持TCP连接
// 适用场合：需要维持登录状态的连续操作
async function scenarioBKeepAlive() {
  console.log('\n=== 场景B：Keep-Alive会话保持（相同IP） ===');
  console.log('技术原理：使用同一个got实例和Agent，保持TCP连接和Keep-Alive');
  console.log('适用场合：需要在会话期间保持相同IP的场景');
  
  const proxyUrl = buildProxyUrl();
  const targetUrl = getEnv('TARGET_URL', 'https://httpbin.org/ip');
  
  // 创建一个Agent实例，复用连接
  const httpsAgent = new HttpsProxyAgent(proxyUrl);
  
  // 创建一个got实例，用于所有请求
  const client = got.extend({
    agent: {
      https: httpsAgent
    },
    headers: {
      'Connection': 'keep-alive',
      'Proxy-Connection': 'keep-alive'
    },
    timeout: {
      request: 15000
    },
    http2: false
  });
  
  for (let i = 1; i <= 3; i++) {
    try {
      const response = await client.get(targetUrl).json();
      const ip = extractIP(response);
      
      console.log(`请求 ${i}: 200 - ${ip}`);
      
      // 短暂延迟但保持连接
      await new Promise(resolve => setTimeout(resolve, 200));
    } catch (error) {
      console.log(`请求 ${i}: 错误 - ${error.message}`);
    }
  }
}

// 场景C：Proxy-Tunnel固定IP（HTTP目标）
//
// 技术原理：在HTTP请求头中添加Proxy-Tunnel标识
// 适用场合：需要使用固定IP访问HTTP目标的场景
async function scenarioCProxyTunnelHttp() {
  console.log('\n=== 场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标） ===');
  console.log('技术原理：在HTTP请求头中添加Proxy-Tunnel标识');
  console.log('适用场合：需要使用固定IP访问HTTP目标的场景');
  
  const proxyUrl = buildProxyUrl();
  const httpTargetUrl = 'http://httpbin.org/ip'; // HTTP目标
  const tunnelId = getEnv('PROXY_TUNNEL', 'nodejs-got-demo-12345');
  
  console.log(`Proxy-Tunnel值: ${tunnelId}`);
  
  // 创建Agent实例，保持会话
  const httpAgent = new HttpProxyAgent(proxyUrl);
  
  // 创建got实例，配置Proxy-Tunnel头
  const client = got.extend({
    agent: {
      http: httpAgent
    },
    headers: {
      'Proxy-Tunnel': tunnelId, // 关键：添加Proxy-Tunnel头（仅对HTTP目标有效）
      'Connection': 'keep-alive',
      'Proxy-Connection': 'keep-alive'
    },
    timeout: {
      request: 15000
    },
    http2: false
  });
  
  for (let i = 1; i <= 3; i++) {
    try {
      const response = await client.get(httpTargetUrl).json();
      const ip = extractIP(response);
      
      console.log(`请求 ${i}: 200 - ${ip}`);
      
      await new Promise(resolve => setTimeout(resolve, 200));
    } catch (error) {
      console.log(`请求 ${i}: 错误 - ${error.message}`);
    }
  }
}

// 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标）
//
// 技术原理：通过https-proxy-agent在CONNECT阶段添加Proxy-Tunnel头
// 适用场合：需要使用固定IP访问HTTPS目标的场景
async function scenarioCProxyTunnelHttps() {
  console.log('\n=== 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标） ===');
  console.log('技术原理：通过https-proxy-agent在CONNECT阶段添加Proxy-Tunnel头');
  console.log('适用场合：需要使用固定IP访问HTTPS目标的场景');
  
  const proxyUrl = buildProxyUrl();
  const targetUrl = getEnv('TARGET_URL', 'https://httpbin.org/ip');
  const tunnelId = getEnv('PROXY_TUNNEL', 'nodejs-got-demo-12345');
  
  console.log('✅ got支持通过https-proxy-agent实现HTTPS Proxy-Tunnel');
  console.log(`Proxy-Tunnel值: ${tunnelId}`);
  
  // 创建支持HTTPS Proxy-Tunnel的Agent
  const httpsAgent = new HttpsProxyAgent(proxyUrl, {
    headers: {
      'Proxy-Tunnel': tunnelId // 关键：在CONNECT阶段发送的头
    }
  });
  
  // 创建got实例，配置Agent
  const client = got.extend({
    agent: {
      https: httpsAgent
    },
    headers: {
      'Connection': 'keep-alive',
      'Proxy-Connection': 'keep-alive'
    },
    timeout: {
      request: 15000
    },
    http2: false
  });
  
  for (let i = 1; i <= 3; i++) {
    try {
      const response = await client.get(targetUrl).json();
      const ip = extractIP(response);
      
      console.log(`请求 ${i}: 200 - ${ip}`);
      
      await new Promise(resolve => setTimeout(resolve, 200));
    } catch (error) {
      console.log(`请求 ${i}: 错误 - ${error.message}`);
    }
  }
}

// 主函数
async function main() {
  console.log('=== Node.js got 隧道代理四种场景演示 ===');
  
  // 显示配置信息
  const host = getEnv('PROXY_HOST', 't.16yun.cn');
  const port = getEnv('PROXY_PORT', '31111');
  const user = getEnv('PROXY_USERNAME') || getEnv('PROXY_USER', 'username');
  const tunnel = getEnv('PROXY_TUNNEL', 'nodejs-got-demo-12345');
  
  console.log(`代理服务器: ${host}:${port}`);
  console.log(`代理用户: ${user}`);
  console.log(`Proxy-Tunnel: ${tunnel}`);
  
  try {
    // 执行四种场景演示
    await scenarioAForceNewConnection();
    await scenarioBKeepAlive();
    await scenarioCProxyTunnelHttp();
    await scenarioCProxyTunnelHttps();
    
    console.log('\n=== 所有场景演示完成 ===');
  } catch (error) {
    console.error('执行错误:', error.message);
    process.exit(1);
  }
}

// 运行主函数
main();
