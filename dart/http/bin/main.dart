import 'dart:io';
import 'dart:convert';
import 'dart:math';
import 'package:http/http.dart' as http;
import 'package:http/io_client.dart';

String env(String name, String fallback) {
  final value = Platform.environment[name]?.trim();
  return value == null || value.isEmpty ? fallback : value;
}

class Session {
  final HttpClient transport = HttpClient();
  final String authorization;
  late final IOClient client;
  Session(String host, int port, String user, String password)
      : authorization = 'Basic ${base64Encode(utf8.encode('$user:$password'))}' {
    transport.connectionTimeout = const Duration(seconds: 10);
    transport.idleTimeout = const Duration(seconds: 15);
    transport.findProxy = (_) => 'PROXY $host:$port';
    client = IOClient(transport);
  }
  Future<String> request(Uri target, bool reuse, String? tunnel) async {
    final request = http.Request('GET', target)..persistentConnection = reuse;
    request.headers['Proxy-Authorization'] = authorization;
    request.headers['Connection'] = reuse ? 'keep-alive' : 'close';
    if (tunnel != null) request.headers['Proxy-Tunnel'] = tunnel;
    final response = await http.Response.fromStream(await client.send(request));
    if (response.statusCode < 200 || response.statusCode >= 300) throw StateError('代理请求: HTTP ${response.statusCode}');
    return response.body;
  }
  void close() {
    client.close();
    transport.close(force: true);
  }
}

Future<void> main() async {
  try {
    final host = env('PROXY_HOST', 't.16yun.cn');
    final port = int.parse(env('PROXY_PORT', '31111'));
    if (port < 1 || port > 65535) throw StateError('PROXY_PORT 必须为有效端口');
    final user = env('PROXY_USERNAME', env('PROXY_USER', 'user'));
    final password = env('PROXY_PASSWORD', env('PROXY_PASS', 'password'));
    final target = Uri.parse(env('TARGET_URL', 'http://httpbin.org/ip'));
    if (target.scheme != 'http' || target.host.isEmpty) throw StateError('本示例仅支持 HTTP，TARGET_URL 不接受 HTTPS');
    final seed = env('PROXY_TUNNEL', Random.secure().nextInt(1 << 32).toString());
    Future<void> group(String name, bool reuse, String? tunnel) async {
      final shared = reuse ? Session(host, port, user, password) : null;
      try {
        for (var index = 1; index <= 2; index++) {
          final client = shared ?? Session(host, port, user, password);
          try {
            final body = await client.request(target, reuse, tunnel).timeout(const Duration(seconds: 15));
            stdout.writeln('$name $index: $body');
          } finally {
            if (shared == null) client.close();
          }
        }
      } finally {
        shared?.close();
      }
    }
    await group('A 新建连接（重新分配不保证不同 IP）', false, null);
    await group('B 连接复用', true, null);
    await group('C-HTTP 同组控制（受出口有效期限制）', false, seed);
    stdout.writeln('本示例为 HTTP-only；HTTPS 及 C-HTTPS 未实现。');
  } catch (failure) {
    stderr.writeln(failure is StateError ? failure.message : '代理请求失败: ${failure.runtimeType}');
    exitCode = 1;
  }
}
