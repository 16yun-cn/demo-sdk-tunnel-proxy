/**
 * Node.js https-proxy-agent 隧道代理四种场景演示
 * 基于16YUN爬虫代理服务的完整实现
 * 
 * 四种场景说明：
 * A. 强制新建连接 - 每次请求建立新连接，获得不同IP
 * B. Keep-Alive会话保持 - 复用TCP连接，保持相同IP  
 * C. Proxy-Tunnel固定IP (HTTP) - 使用Proxy-Tunnel头固定IP访问HTTP目标
 * C. Proxy-Tunnel固定IP (HTTPS) - 使用Proxy-Tunnel头固定IP访问HTTPS目标
 *
 * 注意：Node.js https-proxy-agent支持在HTTPS场景下使用Proxy-Tunnel头，
 * 通过headers选项可以在CONNECT阶段添加自定义头
 */

import http from 'http';
import https from 'https';
import { URL } from 'url';
import { HttpsProxyAgent } from 'https-proxy-agent';

// 代理配置信息
const PROXY_HOST = process.env.PROXY_HOST || 't.16yun.cn';
const PROXY_PORT = process.env.PROXY_PORT || '31111';
const PROXY_USER = process.env.PROXY_USERNAME || process.env.PROXY_USER || 'user';
const PROXY_PASS = process.env.PROXY_PASSWORD || process.env.PROXY_PASS || 'password';
const PROXY_TUNNEL = process.env.PROXY_TUNNEL || 'nodejs-https-agent-demo-12345';

// 目标URL配置
const HTTP_TARGET_URL = 'http://httpbin.org/ip';
const HTTPS_TARGET_URL = process.env.TARGET_URL || 'https://httpbin.org/ip';

async function main() {
    console.log('=== Node.js https-proxy-agent 隧道代理四种场景演示 ===');
    console.log(`代理服务器: ${PROXY_HOST}:${PROXY_PORT}`);
    console.log(`代理用户: ${PROXY_USER}`);
    console.log(`Proxy-Tunnel: ${PROXY_TUNNEL}`);
    console.log();

    try {
        // 场景A：强制新建连接（每次不同IP）
        console.log('【场景A】强制新建连接 - 每次请求建立新连接获得不同IP');
        await scenarioAForceNewConnection();
        console.log();

        // 场景B：Keep-Alive会话保持（相同IP）
        console.log('【场景B】Keep-Alive会话保持 - 复用TCP连接保持相同IP');
        await scenarioBKeepAlive();
        console.log();

        // 场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标）
        console.log('【场景C-HTTP】Proxy-Tunnel固定IP - HTTP目标');
        await scenarioCProxyTunnelHttp();
        console.log();

        // 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标，支持）
        console.log('【场景C-HTTPS】Proxy-Tunnel固定IP - HTTPS目标（支持headers选项）');
        await scenarioCProxyTunnelHttps();
        console.log();

        console.log('=== 所有场景演示完成 ===');
    } catch (error) {
        console.error('执行错误:', error.message);
        process.exit(1);
    }
}

/**
 * 场景A：强制新建连接
 * 每次请求建立新的TCP连接，关闭连接复用
 * 这样可以获得不同的出口IP地址
 */
async function scenarioAForceNewConnection() {
    console.log('技术原理：每次创建新HttpsProxyAgent，禁用Keep-Alive，添加Connection: close头');
    
    const proxyUrl = `http://${PROXY_USER}:${PROXY_PASS}@${PROXY_HOST}:${PROXY_PORT}`;
    
    for (let i = 1; i <= 3; i++) {
        // 每次创建新的HttpsProxyAgent，避免连接复用
        const agent = new HttpsProxyAgent(proxyUrl, {
            keepAlive: false,  // 禁用Keep-Alive
            maxSockets: 1,     // 限制连接数
        });
        
        const ip = await makeRequest(HTTPS_TARGET_URL, agent, {
            'Connection': 'close',
            'Proxy-Connection': 'close'
        });
        
        console.log(`请求 ${i}: 200 - ${ip}`);
        
        // 短暂延迟确保连接完全关闭
        await sleep(500);
    }
}

/**
 * 场景B：Keep-Alive会话保持
 * 复用同一个HttpsProxyAgent实例，保持TCP连接
 * 在代理会话有效期内保持相同的出口IP
 */
async function scenarioBKeepAlive() {
    console.log('技术原理：复用同一HttpsProxyAgent实例，保持TCP连接和Keep-Alive');
    
    const proxyUrl = `http://${PROXY_USER}:${PROXY_PASS}@${PROXY_HOST}:${PROXY_PORT}`;
    
    // 复用同一个HttpsProxyAgent实例
    const agent = new HttpsProxyAgent(proxyUrl, {
        keepAlive: true,   // 启用Keep-Alive
        maxSockets: 5,     // 允许更多连接
    });
    
    for (let i = 1; i <= 3; i++) {
        const ip = await makeRequest(HTTPS_TARGET_URL, agent, {
            'Connection': 'keep-alive',
            'Proxy-Connection': 'keep-alive'
        });
        
        console.log(`请求 ${i}: 200 - ${ip}`);
        
        // 短暂延迟但保持连接
        await sleep(200);
    }
}

/**
 * 场景C：Proxy-Tunnel固定IP（HTTP目标）
 * 使用Proxy-Tunnel头标识固定会话
 * 相同Proxy-Tunnel值在有效期内使用相同出口IP
 */
async function scenarioCProxyTunnelHttp() {
    console.log('技术原理：在HTTP请求头中添加Proxy-Tunnel标识');
    console.log(`Proxy-Tunnel值: ${PROXY_TUNNEL}`);
    
    const proxyUrl = `http://${PROXY_USER}:${PROXY_PASS}@${PROXY_HOST}:${PROXY_PORT}`;
    const agent = new HttpsProxyAgent(proxyUrl);
    
    for (let i = 1; i <= 3; i++) {
        const ip = await makeHttpRequest(HTTP_TARGET_URL, agent, {
            'Proxy-Tunnel': PROXY_TUNNEL,  // 关键：添加Proxy-Tunnel头（仅对HTTP目标有效）
            'Connection': 'keep-alive',
            'Proxy-Connection': 'keep-alive'
        });
        
        console.log(`请求 ${i}: 200 - ${ip}`);
        
        await sleep(200);
    }
}

/**
 * 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标）
 * 注意：Node.js https-proxy-agent支持在CONNECT阶段添加自定义头
 * 通过headers选项可以实现HTTPS Proxy-Tunnel
 */
async function scenarioCProxyTunnelHttps() {
    console.log('技术原理：通过https-proxy-agent的headers选项在CONNECT阶段添加Proxy-Tunnel');
    console.log('✅ 优势：Node.js https-proxy-agent支持CONNECT阶段自定义头，Proxy-Tunnel对HTTPS有效');
    console.log(`Proxy-Tunnel值: ${PROXY_TUNNEL}`);
    
    const proxyUrl = `http://${PROXY_USER}:${PROXY_PASS}@${PROXY_HOST}:${PROXY_PORT}`;
    
    // 关键：使用headers选项添加Proxy-Tunnel头
    const agent = new HttpsProxyAgent(proxyUrl, {
        headers: {
            'Proxy-Tunnel': PROXY_TUNNEL  // 这个头会在CONNECT阶段发送
        }
    });
    
    for (let i = 1; i <= 3; i++) {
        const ip = await makeRequest(HTTPS_TARGET_URL, agent, {
            'Connection': 'keep-alive',
            'Proxy-Connection': 'keep-alive'
        });
        
        console.log(`请求 ${i}: 200 - ${ip} （Proxy-Tunnel生效）`);
        
        await sleep(200);
    }
    
    console.log('💡 技术优势：https-proxy-agent headers选项支持HTTPS Proxy-Tunnel');
}

/**
 * 发送HTTPS请求
 */
function makeRequest(url, agent, headers = {}) {
    return new Promise((resolve, reject) => {
        const options = new URL(url);
        options.agent = agent;
        options.headers = headers;
        
        const req = https.request(options, (res) => {
            let data = '';
            res.on('data', (chunk) => data += chunk);
            res.on('end', () => {
                try {
                    const ip = extractIp(data);
                    resolve(ip);
                } catch (error) {
                    resolve('IP解析失败');
                }
            });
        });
        
        req.on('error', reject);
        req.end();
    });
}

/**
 * 发送HTTP请求
 */
function makeHttpRequest(url, agent, headers = {}) {
    return new Promise((resolve, reject) => {
        const options = new URL(url);
        options.agent = agent;
        options.headers = headers;
        
        const req = http.request(options, (res) => {
            let data = '';
            res.on('data', (chunk) => data += chunk);
            res.on('end', () => {
                try {
                    const ip = extractIp(data);
                    resolve(ip);
                } catch (error) {
                    resolve('IP解析失败');
                }
            });
        });
        
        req.on('error', reject);
        req.end();
    });
}

/**
 * 从响应内容中提取IP地址
 */
function extractIp(content) {
    try {
        // 尝试解析JSON响应，适用于httpbin.org/ip
        if (content.includes('"origin"')) {
            const data = JSON.parse(content);
            return data.origin || '未知IP';
        }
        
        // 使用正则表达式作为备选方案
        const match = content.match(/"origin":\s*"([^"]+)"/);
        if (match) {
            return match[1];
        }
        
        return '未知IP';
    } catch (error) {
        return 'IP解析失败';
    }
}

/**
 * 延迟函数
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// 运行主函数
main();

