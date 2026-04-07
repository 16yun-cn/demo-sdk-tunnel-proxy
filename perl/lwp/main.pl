#!/usr/bin/env perl

# 16YUN(亿牛云) Perl LWP::UserAgent 隧道代理演示
#
# 本示例演示四种隧道代理使用场景：
# - 场景A：每次新建连接（强制IP切换）
# - 场景B：Keep-Alive会话保持（相同IP）
# - 场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标）
# - 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标）⚠️ 需验证

use strict;
use warnings;
use LWP::UserAgent;
use JSON;
use Time::HiRes qw(sleep);

# 代理配置信息
sub get_proxy_config {
    my %config = (
        host     => $ENV{PROXY_HOST}     || 't.16yun.cn',
        port     => $ENV{PROXY_PORT}     || '31111',
        username => $ENV{PROXY_USERNAME} || $ENV{PROXY_USER} || 'user',
        password => $ENV{PROXY_PASSWORD} || $ENV{PROXY_PASS} || 'password',
        tunnel   => $ENV{PROXY_TUNNEL}   || 'perl-lwp-demo-12345',
    );
    
    die "PROXY_USERNAME and PROXY_PASSWORD must be provided" 
        if !$config{username} || !$config{password};
    
    $config{proxy_url} = "http://$config{username}:$config{password}\@$config{host}:$config{port}";
    
    return \%config;
}

# 从响应中提取IP地址
sub extract_ip {
    my ($content) = @_;
    
    eval {
        my $data = decode_json($content);
        return $data->{origin} if $data->{origin};
    };
    
    return '未知IP';
}

# 场景A：强制新建连接（每次不同IP）
sub scenario_a_force_new_connection {
    my ($config) = @_;
    
    print "\n=== 场景A：强制新建连接（强制IP切换） ===\n";
    print "技术原理：每次请求创建新的LWP::UserAgent实例，强制断开连接\n";
    print "适用场合：需要每个请求都使用不同IP的场景\n";
    
    my $target_url = $ENV{TARGET_URL} || 'https://httpbin.org/ip';
    
    for my $i (1..3) {
        # 每次创建新的UserAgent实例
        my $ua = LWP::UserAgent->new(
            timeout => 15,
            agent   => 'PerlLWP/1.0',
        );
        
        # 设置代理
        $ua->proxy(['http', 'https'], $config->{proxy_url});
        
        # 添加强制关闭连接的头部
        $ua->default_header('Connection' => 'close');
        $ua->default_header('Proxy-Connection' => 'close');
        
        my $response = $ua->get($target_url);
        
        if ($response->is_success) {
            my $ip = extract_ip($response->decoded_content);
            print "请求 $i: " . $response->code . " - $ip\n";
        } else {
            print "请求 $i: 错误 - " . $response->status_line . "\n";
        }
        
        # 短暂延迟确保连接完全关闭
        sleep(0.5);
    }
}

# 场景B：Keep-Alive会话保持（相同IP）
sub scenario_b_keep_alive {
    my ($config) = @_;
    
    print "\n=== 场景B：Keep-Alive会话保持（相同IP） ===\n";
    print "技术原理：使用同一个LWP::UserAgent实例，保持TCP连接和Keep-Alive\n";
    print "适用场合：需要在会话期间保持相同IP的场景\n";
    
    my $target_url = $ENV{TARGET_URL} || 'https://httpbin.org/ip';
    
    # 创建一个UserAgent实例，用于所有请求
    my $ua = LWP::UserAgent->new(
        timeout     => 15,
        agent       => 'PerlLWP/1.0',
        keep_alive  => 10,  # 关键：启用Keep-Alive
    );
    
    # 设置代理
    $ua->proxy(['http', 'https'], $config->{proxy_url});
    
    # 添加Keep-Alive头部
    $ua->default_header('Connection' => 'keep-alive');
    $ua->default_header('Proxy-Connection' => 'keep-alive');
    
    for my $i (1..3) {
        my $response = $ua->get($target_url);
        
        if ($response->is_success) {
            my $ip = extract_ip($response->decoded_content);
            print "请求 $i: " . $response->code . " - $ip\n";
        } else {
            print "请求 $i: 错误 - " . $response->status_line . "\n";
        }
        
        # 短暂延迟但保持连接
        sleep(0.2);
    }
}

# 场景C：Proxy-Tunnel固定IP（HTTP目标）
sub scenario_c_proxy_tunnel_http {
    my ($config) = @_;
    
    print "\n=== 场景C-HTTP：Proxy-Tunnel固定IP（HTTP目标） ===\n";
    print "技术原理：在HTTP请求头中添加Proxy-Tunnel标识\n";
    print "适用场合：需要使用固定IP访问HTTP目标的场景\n";
    
    # HTTP目标（用于Proxy-Tunnel演示）
    my $http_target_url = 'http://httpbin.org/ip';
    
    print "Proxy-Tunnel值: $config->{tunnel}\n";
    
    # 创建UserAgent实例，保持会话
    my $ua = LWP::UserAgent->new(
        timeout     => 15,
        agent       => 'PerlLWP/1.0',
        keep_alive  => 10,
    );
    
    # 设置代理
    $ua->proxy(['http'], $config->{proxy_url});
    
    # 添加Proxy-Tunnel头（仅对HTTP目标有效）
    $ua->default_header('Proxy-Tunnel' => $config->{tunnel});
    $ua->default_header('Connection' => 'keep-alive');
    $ua->default_header('Proxy-Connection' => 'keep-alive');
    
    for my $i (1..3) {
        my $response = $ua->get($http_target_url);
        
        if ($response->is_success) {
            my $ip = extract_ip($response->decoded_content);
            print "请求 $i: " . $response->code . " - $ip\n";
        } else {
            print "请求 $i: 错误 - " . $response->status_line . "\n";
        }
        
        sleep(0.2);
    }
}

# 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标）
sub scenario_c_proxy_tunnel_https {
    my ($config) = @_;
    
    print "\n=== 场景C-HTTPS：Proxy-Tunnel固定IP（HTTPS目标） ===\n";
    print "技术原理：尝试通过LWP::UserAgent在CONNECT阶段添加Proxy-Tunnel头\n";
    print "适用场合：需要使用固定IP访问HTTPS目标的场景\n";
    
    my $target_url = $ENV{TARGET_URL} || 'https://httpbin.org/ip';
    
    print "⚠️  Perl LWP::UserAgent的HTTPS Proxy-Tunnel支持需要验证\n";
    print "Proxy-Tunnel值: $config->{tunnel}\n";
    
    # 创建UserAgent实例，尝试HTTPS Proxy-Tunnel
    my $ua = LWP::UserAgent->new(
        timeout     => 15,
        agent       => 'PerlLWP/1.0',
        keep_alive  => 10,
    );
    
    # 设置代理
    $ua->proxy(['https'], $config->{proxy_url});
    
    # 尝试添加Proxy-Tunnel头（注意：这个头可能不会在CONNECT阶段发送）
    $ua->default_header('Proxy-Tunnel' => $config->{tunnel});
    $ua->default_header('Connection' => 'keep-alive');
    $ua->default_header('Proxy-Connection' => 'keep-alive');
    
    for my $i (1..3) {
        my $response = $ua->get($target_url);
        
        if ($response->is_success) {
            my $ip = extract_ip($response->decoded_content);
            print "请求 $i: " . $response->code . " - $ip （HTTPS Proxy-Tunnel效果待验证）\n";
        } else {
            print "请求 $i: 错误 - " . $response->status_line . "\n";
        }
        
        sleep(0.2);
    }
    
    print "💡 建议：如需确保HTTPS Proxy-Tunnel支持，请使用支持的语言如Go、Python或Node.js\n";
}

# 主程序
sub main {
    print "=== Perl LWP::UserAgent 隧道代理四种场景演示 ===\n";
    
    eval {
        my $config = get_proxy_config();
        
        print "代理服务器: $config->{host}:$config->{port}\n";
        print "代理用户: $config->{username}\n";
        print "Proxy-Tunnel: $config->{tunnel}\n";
        
        # 执行四种场景演示
        scenario_a_force_new_connection($config);
        scenario_b_keep_alive($config);
        scenario_c_proxy_tunnel_http($config);
        scenario_c_proxy_tunnel_https($config);
        
        print "\n=== 所有场景演示完成 ===\n";
    };
    
    if ($@) {
        print "配置错误: $@\n";
        exit(1);
    }
}

# 运行主程序
main();
