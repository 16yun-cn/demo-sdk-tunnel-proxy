package cn.y16yun.demo.httpclient4;

import java.net.URI;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.UUID;


public final class Main {
    static String host, user, password; static int port;
    static String env(String name, String fallback) {
        String value = System.getenv(name);
        return value == null || value.trim().isEmpty() ? fallback : value.trim();
    }
    static String target(String value, boolean httpOnly) throws Exception {
        String scheme = new URI(value).getScheme();
        if (!("http".equalsIgnoreCase(scheme) || (!httpOnly && "https".equalsIgnoreCase(scheme))))
            throw new IllegalStateException(httpOnly ? "TARGET_URL_HTTP 必须为 HTTP" : "TARGET_URL 必须为 HTTP 或 HTTPS");
        return value;
    }
    static final class Session implements AutoCloseable {
        final org.apache.http.impl.client.CloseableHttpClient client;
        Session() {
            org.apache.http.impl.client.BasicCredentialsProvider credentials = new org.apache.http.impl.client.BasicCredentialsProvider();
            credentials.setCredentials(new org.apache.http.auth.AuthScope(host, port),
                new org.apache.http.auth.UsernamePasswordCredentials(user, password));
            org.apache.http.client.config.RequestConfig config = org.apache.http.client.config.RequestConfig.custom()
                .setProxy(new org.apache.http.HttpHost(host, port)).setConnectTimeout(10000)
                .setSocketTimeout(10000).setConnectionRequestTimeout(10000).build();
            client = org.apache.http.impl.client.HttpClients.custom().setDefaultCredentialsProvider(credentials)
                .setDefaultRequestConfig(config).disableAutomaticRetries().build();
        }
        String request(String url, boolean close, String tunnel) throws Exception {
            org.apache.http.client.methods.HttpGet request = new org.apache.http.client.methods.HttpGet(url);
            request.setHeader("Connection", close ? "close" : "keep-alive");
            if (tunnel != null) request.setHeader("Proxy-Tunnel", tunnel);
            try (org.apache.http.client.methods.CloseableHttpResponse response = client.execute(request)) {
                int status = response.getStatusLine().getStatusCode();
                if (status < 200 || status >= 300) throw new IllegalStateException("代理请求: HTTP " + status);
                return org.apache.http.util.EntityUtils.toString(response.getEntity(), StandardCharsets.UTF_8);
            }
        }
        public void close() throws IOException { client.close(); }
    }
    static void group(String name, String target, boolean reuse, String tunnel) throws Exception {
        Session shared = reuse ? new Session() : null;
        try {
            for (int i = 1; i <= 2; i++) {
                Session client = shared == null ? new Session() : shared;
                try { System.out.println(name + " " + i + ": " + client.request(target, !reuse, tunnel)); }
                finally { if (shared == null) client.close(); }
            }
        } finally { if (shared != null) shared.close(); }
    }
    public static void main(String[] args) {
        try {
            host = env("PROXY_HOST", "t.16yun.cn"); port = Integer.parseInt(env("PROXY_PORT", "31111"));
            if (port < 1 || port > 65535) throw new IllegalStateException("PROXY_PORT 必须为有效端口");
            user = env("PROXY_USERNAME", env("PROXY_USER", "user")); password = env("PROXY_PASSWORD", env("PROXY_PASS", "password"));
            String target = target(env("TARGET_URL", "https://httpbin.org/ip"), false);
            String http = target(env("TARGET_URL_HTTP", target.startsWith("http://") ? target : "http://httpbin.org/ip"), true);
            String seed = env("PROXY_TUNNEL", UUID.randomUUID().toString());

            group("A 新建连接（重新分配不保证不同 IP）", target, false, null);
            group("B 连接复用", target, true, null);
            group("C-HTTP 同组控制（受出口有效期限制）", http, false, seed);
            System.out.println("C-HTTPS 未实现：普通 HTTPS 代理认证不代表支持 CONNECT 自定义头。");
        } catch (Exception failure) {
            System.err.println(failure instanceof IllegalStateException ? failure.getMessage() : "代理请求失败: " + failure.getClass().getSimpleName());
            System.exit(1);
        }
    }
}
