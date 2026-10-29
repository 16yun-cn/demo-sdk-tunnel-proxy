package cn.y16yun.demo.httpurlconnection;

import java.net.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;


public final class Main {
    static String host, user, password; static int port;
    static final ThreadLocal<Integer> authAttempts = ThreadLocal.withInitial(() -> 0);
    static String env(String name, String fallback) {
        String value = System.getenv(name);
        return value == null || value.trim().isEmpty() ? fallback : value.trim();
    }
    static String basic() { return "Basic " + Base64.getEncoder().encodeToString((user + ":" + password).getBytes(StandardCharsets.UTF_8)); }
    static void configureJdkProxyAuth() {
        System.setProperty("jdk.http.auth.tunneling.disabledSchemes", "");
        System.setProperty("jdk.http.auth.proxying.disabledSchemes", "");
        java.net.Authenticator.setDefault(new java.net.Authenticator() {
            protected PasswordAuthentication getPasswordAuthentication() {
                if (getRequestorType() != RequestorType.PROXY || !host.equalsIgnoreCase(getRequestingHost()) || port != getRequestingPort() || authAttempts.get() >= 1) return null;
                authAttempts.set(authAttempts.get() + 1);
                return new PasswordAuthentication(user, password.toCharArray());
            }
        });
    }
    static String target(String value, boolean httpOnly) throws Exception {
        String scheme = new URI(value).getScheme();
        if (!("http".equalsIgnoreCase(scheme) || (!httpOnly && "https".equalsIgnoreCase(scheme))))
            throw new IllegalStateException(httpOnly ? "TARGET_URL_HTTP 必须为 HTTP" : "TARGET_URL 必须为 HTTP 或 HTTPS");
        return value;
    }
    static final class Session implements AutoCloseable {
        String request(String url, boolean close, String tunnel) throws Exception {
            authAttempts.set(0);
            HttpURLConnection connection = (HttpURLConnection)new URL(url).openConnection(
                new Proxy(Proxy.Type.HTTP, new InetSocketAddress(host, port)));
            connection.setConnectTimeout(10000); connection.setReadTimeout(10000);
            connection.setRequestProperty("Connection", close ? "close" : "keep-alive");
            connection.setRequestProperty("Proxy-Connection", close ? "close" : "keep-alive");
            if (url.startsWith("http://")) connection.setRequestProperty("Proxy-Authorization", basic());
            if (tunnel != null) connection.setRequestProperty("Proxy-Tunnel", tunnel);
            try {
                int status = connection.getResponseCode();
                if (status < 200 || status >= 300) throw new IllegalStateException("代理请求: HTTP " + status);
                ByteArrayOutputStream body = new ByteArrayOutputStream();
                try (InputStream input = connection.getInputStream()) {
                    byte[] buffer = new byte[8192]; int count;
                    while ((count = input.read(buffer)) != -1) body.write(buffer, 0, count);
                }
                return new String(body.toByteArray(), StandardCharsets.UTF_8);
            } finally { if (close) connection.disconnect(); }
        }
        public void close() { /* Fully consumed B responses return their connection to the JDK cache. */ }
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
            configureJdkProxyAuth();
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
