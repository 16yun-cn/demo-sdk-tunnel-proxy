// 16YUN(亿牛云) Node.js undici 隧道代理演示
//
// 本示例演示四种隧道代理使用场景：
// - 场景A：每次新建连接（强制IP切换）
// - 场景B：Keep-Alive会话保持（相同IP）
// - 场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标）
// - 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标）⚠️ 需验证
//
// 技术特点：
// - undici是高性能HTTP客户端，需要验证HTTPS Proxy-Tunnel支持情况
// - 完整的四种场景实现，覆盖所有代理使用模式
// - 详细的中文注释和技术原理说明

import { request, Client, ProxyAgent } from 'undici';

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

function buildProxyOrigin() {
  const host = getEnv('PROXY_HOST', 't.16yun.cn');
  const port = getEnv('PROXY_PORT', '31111');
  return `http://${host}:${port}`;
}

function buildProxyAuthorization() {
  const { user, pass } = buildProxyAuth();
  return `Basic ${Buffer.from(`${user}:${pass}`).toString('base64')}`;
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
// 技术原理：每次请求使用新的Agent或直接调用request，不复用连接
// 适用场合：需要每个请求都使用不同IP的场景
async function scenarioAForceNewConnection() {
  console.log('\n=== 场景A：每次新建连接（强制IP切换） ===');
  console.log('技术原理：每次请求使用新的ProxyAgent，强制断开连接');
  console.log('适用场合：需要每个请求都使用不同IP的场景');
  
  const proxyUrl = buildProxyUrl();
  const targetUrl = getEnv('TARGET_URL', 'https://httpbin.org/ip');
  
  for (let i = 1; i <= 3; i++) {
    try {
      // 每次创建新的Client实例，强制断开连接
      const proxyClient = new Client(buildProxyOrigin());
      
      const response = await proxyClient.request({
        method: 'GET',
        path: targetUrl,
        headers: {
          'proxy-authorization': buildProxyAuthorization(),
          'Connection': 'close',
          'Proxy-Connection': 'close'
        },
        headersTimeout: 15000,
        bodyTimeout: 15000
      });
      
      const data = await response.body.json();
      const ip = extractIP(data);
      
      console.log(`请求 ${i}: ${response.statusCode} - ${ip}`);
      
      // 关闭Client释放连接
      await proxyClient.close();
      
      // 短暂延迟确保连接完全关闭
      await new Promise(resolve => setTimeout(resolve, 500));
    } catch (error) {
      console.log(`请求 ${i}: 错误 - ${error.message}`);
    }
  }
}

// 场景B：Keep-Alive会话保持（相同IP）
//
// 技术原理：使用同一个ProxyAgent实例，保持TCP连接
// 适用场合：需要维持登录状态的连续操作
async function scenarioBKeepAlive() {
  console.log('\n=== 场景B：Keep-Alive会话保持（相同IP） ===');
  console.log('技术原理：使用同一个ProxyAgent实例，保持TCP连接和Keep-Alive');
  console.log('适用场合：需要在会话期间保持相同IP的场景');
  
  const proxyUrl = buildProxyUrl();
  const targetUrl = getEnv('TARGET_URL', 'https://httpbin.org/ip');
  
  // 创建一个Client实例，复用连接
  const proxyClient = new Client(buildProxyOrigin());
  
  try {
    for (let i = 1; i <= 3; i++) {
      try {
        const response = await proxyClient.request({
          method: 'GET',
          path: targetUrl,
          headers: {
            'proxy-authorization': buildProxyAuthorization(),
            'Connection': 'keep-alive',
            'Proxy-Connection': 'keep-alive'
          },
          headersTimeout: 15000,
          bodyTimeout: 15000
        });
        
        const data = await response.body.json();
        const ip = extractIP(data);
        
        console.log(`请求 ${i}: ${response.statusCode} - ${ip}`);
        
        // 短暂延迟但保持连接
        await new Promise(resolve => setTimeout(resolve, 200));
      } catch (error) {
        console.log(`请求 ${i}: 错误 - ${error.message}`);
      }
    }
  } finally {
    // 最后关闭Client
    await proxyClient.close();
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
  
  const proxyOrigin = buildProxyOrigin();
  const httpTargetUrl = 'http://httpbin.org/ip'; // HTTP目标
  const tunnelId = getEnv('PROXY_TUNNEL', 'nodejs-undici-demo-12345');
  
  console.log(`Proxy-Tunnel值: ${tunnelId}`);
  
  // 创建Client实例，保持会话
  const proxyClient = new Client(proxyOrigin);
  
  try {
    for (let i = 1; i <= 3; i++) {
      try {
        const response = await proxyClient.request({
          method: 'GET',
          path: httpTargetUrl,
          headers: {
            'proxy-authorization': buildProxyAuthorization(),
            'Proxy-Tunnel': tunnelId,
            'Connection': 'keep-alive',
            'Proxy-Connection': 'keep-alive'
          },
          headersTimeout: 15000,
          bodyTimeout: 15000
        });
        
        const data = await response.body.json();
        const ip = extractIP(data);
        
        console.log(`请求 ${i}: ${response.statusCode} - ${ip}`);
        
        await new Promise(resolve => setTimeout(resolve, 200));
      } catch (error) {
        console.log(`请求 ${i}: 错误 - ${error.message}`);
      }
    }
  } finally {
    await proxyClient.close();
  }
}

// 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标）
//
// 技术原理：尝试通过ProxyAgent在CONNECT阶段添加Proxy-Tunnel头
// 注意：undici的HTTPS Proxy-Tunnel支持需要验证
async function scenarioCProxyTunnelHttps() {
  console.log('\n=== 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标） ===');
  console.log('技术原理：尝试通过ProxyAgent在CONNECT阶段添加Proxy-Tunnel头');
  console.log('适用场合：需要使用固定IP访问HTTPS目标的场景');
  
  const proxyUrl = buildProxyUrl();
  const targetUrl = getEnv('TARGET_URL', 'https://httpbin.org/ip');
  const tunnelId = getEnv('PROXY_TUNNEL', 'nodejs-undici-demo-12345');
  
  console.log('⚠️  undici的HTTPS Proxy-Tunnel支持需要验证');
  console.log(`Proxy-Tunnel值: ${tunnelId}`);
  
  // 尝试使用ProxyAgent配置CONNECT头
  // 注意：undici的ProxyAgent可能不支持自定义CONNECT头
  try {
    const proxyAgent = new ProxyAgent({
      uri: proxyUrl,
      token: buildProxyAuthorization(),
      headers: {
        'Proxy-Tunnel': tunnelId
      }
    });
    
    try {
      for (let i = 1; i <= 3; i++) {
        try {
          const response = await request(targetUrl, {
            dispatcher: proxyAgent,
            headers: {
              'Connection': 'keep-alive',
              'Proxy-Connection': 'keep-alive'
            },
            headersTimeout: 15000,
            bodyTimeout: 15000
          });
          
          const data = await response.body.json();
          const ip = extractIP(data);
          
          console.log(`请求 ${i}: ${response.statusCode} - ${ip} （HTTPS Proxy-Tunnel效果待验证）`);
          
          await new Promise(resolve => setTimeout(resolve, 200));
        } catch (error) {
          console.log(`请求 ${i}: 错误 - ${error.message}`);
        }
      }
    } finally {
      await proxyAgent.close();
    }
  } catch (error) {
    console.log('⚠️  undici可能不支持自定义CONNECT头配置');
    console.log('💡 建议：如需HTTPS Proxy-Tunnel，请使用got、axios或https-proxy-agent');
    console.log(`错误信息: ${error.message}`);
    
    // 降级到普通HTTPS代理（不支持Proxy-Tunnel）
    console.log('\n降级处理：使用普通HTTPS代理（无Proxy-Tunnel）');
    const proxyAgent = new ProxyAgent(proxyUrl);
    
    try {
      for (let i = 1; i <= 3; i++) {
        try {
          const response = await request(targetUrl, {
            dispatcher: proxyAgent,
            headers: {
              'Connection': 'keep-alive',
              'Proxy-Connection': 'keep-alive'
            },
            headersTimeout: 15000,
            bodyTimeout: 15000
          });
          
          const data = await response.body.json();
          const ip = extractIP(data);
          
          console.log(`请求 ${i}: ${response.statusCode} - ${ip} （无Proxy-Tunnel）`);
          
          await new Promise(resolve => setTimeout(resolve, 200));
        } catch (error) {
          console.log(`请求 ${i}: 错误 - ${error.message}`);
        }
      }
    } finally {
      await proxyAgent.close();
    }
  }
}

// 主函数
async function main() {
  console.log('=== Node.js undici 隧道代理四种场景演示 ===');
  
  // 显示配置信息
  const host = getEnv('PROXY_HOST', 't.16yun.cn');
  const port = getEnv('PROXY_PORT', '31111');
  const user = getEnv('PROXY_USERNAME') || getEnv('PROXY_USER', 'username');
  const tunnel = getEnv('PROXY_TUNNEL', 'nodejs-undici-demo-12345');
  
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
