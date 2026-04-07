#!/usr/bin/env ruby
#
# Ruby Faraday 隧道代理四种场景演示
# 基于16YUN爬虫代理服务的完整实现
# 
# 四种场景说明：
# A. 强制新建连接 - 每次请求建立新连接，获得不同IP
# B. Keep-Alive会话保持 - 复用TCP连接，保持相同IP  
# C. Proxy-Tunnel固定IP (HTTP) - 使用Proxy-Tunnel头固定IP访问HTTP目标
# C. Proxy-Tunnel固定IP (HTTPS) - 使用Proxy-Tunnel头固定IP访问HTTPS目标
#
# 注意：Ruby Faraday基于Net::HTTP，不支持在HTTPS CONNECT阶段添加自定义头，
# 因此HTTPS Proxy-Tunnel场景无法生效，仅作演示

require 'faraday'
require 'json'

# 代理配置信息
PROXY_HOST = ENV['PROXY_HOST'] || 't.16yun.cn'
PROXY_PORT = (ENV['PROXY_PORT'] || '31111').to_i
PROXY_USER = ENV['PROXY_USERNAME'] || ENV['PROXY_USER'] || 'user'
PROXY_PASS = ENV['PROXY_PASSWORD'] || ENV['PROXY_PASS'] || 'password'
PROXY_TUNNEL = ENV['PROXY_TUNNEL'] || 'ruby-faraday-demo-12345'
PROXY_URL = "http://#{PROXY_USER}:#{PROXY_PASS}@#{PROXY_HOST}:#{PROXY_PORT}"

# 目标URL配置
HTTP_TARGET_URL = 'http://httpbin.org/ip'
HTTPS_TARGET_URL = ENV['TARGET_URL'] || 'https://httpbin.org/ip'

def main
  puts "=== Ruby Faraday 隧道代理四种场景演示 ==="
  puts "代理服务器: #{PROXY_HOST}:#{PROXY_PORT}"
  puts "代理用户: #{PROXY_USER}"
  puts "Proxy-Tunnel: #{PROXY_TUNNEL}"
  puts

  begin
    # 场景A：强制新建连接（每次不同IP）
    puts "【场景A】强制新建连接 - 每次请求建立新连接获得不同IP"
    scenario_a_force_new_connection
    puts

    # 场景B：Keep-Alive会话保持（相同IP）
    puts "【场景B】Keep-Alive会话保持 - 复用TCP连接保持相同IP"
    scenario_b_keep_alive
    puts

    # 场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标）
    puts "【场景C-HTTP】Proxy-Tunnel固定IP - HTTP目标"
    scenario_c_proxy_tunnel_http
    puts

    # 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标，不支持）
    puts "【场景C-HTTPS】Proxy-Tunnel固定IP - HTTPS目标（不支持CONNECT自定义头）"
    scenario_c_proxy_tunnel_https
    puts

    puts "=== 所有场景演示完成 ==="
  rescue => e
    $stderr.puts "执行错误: #{e.message}"
    exit(1)
  end
end

#
# 场景A：强制新建连接
# 每次请求建立新的TCP连接，关闭连接复用
# 这样可以获得不同的出口IP地址
#
def scenario_a_force_new_connection
  puts "技术原理：每次创建新的Faraday实例，强制关闭连接复用"
  
  3.times do |i|
    # 每次创建新的Faraday实例，禁用连接复用
    conn = Faraday.new do |f|
      f.request :url_encoded
      f.adapter Faraday.default_adapter
      f.options.timeout = 15
      f.proxy = PROXY_URL
      f.headers['Connection'] = 'close'
      f.headers['Proxy-Connection'] = 'close'
    end
    
    response = conn.get(HTTPS_TARGET_URL)
    
    content = response.body
    ip = extract_ip(content)
    
    puts "请求 #{i + 1}: #{response.status} - #{ip}"
    
    # 短暂延迟确保连接完全关闭
    sleep(0.5)
  end
end

#
# 场景B：Keep-Alive会话保持
# 复用同一个Faraday实例，保持TCP连接
# 在代理会话有效期内保持相同的出口IP
#
def scenario_b_keep_alive
  puts "技术原理：使用同一个Faraday实例，保持TCP连接和Keep-Alive"
  
  # 创建一个保持连接的Faraday实例
  conn = Faraday.new do |f|
    f.request :url_encoded
    f.adapter Faraday.default_adapter
    f.options.timeout = 15
    f.proxy = PROXY_URL
    f.headers['Connection'] = 'keep-alive'
    f.headers['Proxy-Connection'] = 'keep-alive'
  end
  
  3.times do |i|
    response = conn.get(HTTPS_TARGET_URL)
    
    content = response.body
    ip = extract_ip(content)
    
    puts "请求 #{i + 1}: #{response.status} - #{ip}"
    
    # 短暂延迟但保持连接
    sleep(0.2)
  end
end

#
# 场景C：Proxy-Tunnel固定IP（HTTP目标）
# 使用Proxy-Tunnel头标识固定会话
# 相同Proxy-Tunnel值在有效期内使用相同出口IP
#
def scenario_c_proxy_tunnel_http
  puts "技术原理：在HTTP请求头中添加Proxy-Tunnel标识"
  puts "Proxy-Tunnel值: #{PROXY_TUNNEL}"
  
  # 创建带Proxy-Tunnel头的Faraday实例
  conn = Faraday.new do |f|
    f.request :url_encoded
    f.adapter Faraday.default_adapter
    f.options.timeout = 15
    f.proxy = PROXY_URL
    f.headers['Proxy-Tunnel'] = PROXY_TUNNEL # 关键：添加Proxy-Tunnel头（仅对HTTP目标有效）
    f.headers['Connection'] = 'keep-alive'
    f.headers['Proxy-Connection'] = 'keep-alive'
  end
  
  3.times do |i|
    response = conn.get(HTTP_TARGET_URL)
    
    content = response.body
    ip = extract_ip(content)
    
    puts "请求 #{i + 1}: #{response.status} - #{ip}"
    
    sleep(0.2)
  end
end

#
# 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标）
# 注意：Ruby Faraday基于Net::HTTP，不支持在CONNECT阶段添加自定义头
# 因此Proxy-Tunnel对HTTPS目标无效，这里仅作演示
#
def scenario_c_proxy_tunnel_https
  puts "技术原理：尝试在HTTPS请求中使用Proxy-Tunnel（注意：不会生效）"
  puts "⚠️  警告：Ruby Faraday基于Net::HTTP，不支持CONNECT阶段自定义头，Proxy-Tunnel对HTTPS无效"
  puts "Proxy-Tunnel值: #{PROXY_TUNNEL}"
  
  # 创建尝试使用Proxy-Tunnel的Faraday实例（对HTTPS无效）
  conn = Faraday.new do |f|
    f.request :url_encoded
    f.adapter Faraday.default_adapter
    f.options.timeout = 15
    f.proxy = PROXY_URL
    f.headers['Proxy-Tunnel'] = PROXY_TUNNEL # 注意：这个头不会在CONNECT阶段发送
    f.headers['Connection'] = 'keep-alive'
    f.headers['Proxy-Connection'] = 'keep-alive'
  end
  
  3.times do |i|
    response = conn.get(HTTPS_TARGET_URL)
    
    content = response.body
    ip = extract_ip(content)
    
    puts "请求 #{i + 1}: #{response.status} - #{ip} （Proxy-Tunnel未生效）"
    
    sleep(0.2)
  end
  
  puts "💡 建议：如需HTTPS Proxy-Tunnel，请使用支持的语言如Go、Python或Node.js"
end

#
# 从响应内容中提取IP地址
#
def extract_ip(content)
  begin
    # 尝试解析JSON响应，适用于httpbin.org/ip
    if content.include?('"origin"')
      json_data = JSON.parse(content)
      return json_data['origin'] if json_data['origin']
    end
    
    # 使用正则表达式作为备选方案
    match = content.match(/"origin":\s*"([^"]+)"/)
    return match[1] if match
    
    "未知IP"
  rescue => e
    "IP解析失败"
  end
end

# 运行主函数
main
