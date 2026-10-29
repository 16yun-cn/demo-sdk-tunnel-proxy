import okhttp3.Credentials
import okhttp3.OkHttpClient
import okhttp3.Request
import java.net.InetSocketAddress
import java.net.Proxy
import java.net.URI
import java.util.UUID
import java.util.concurrent.TimeUnit

fun env(name: String, fallback: String? = null): String? = System.getenv(name)?.trim()?.takeIf { it.isNotEmpty() } ?: fallback
fun target(value: String, httpOnly: Boolean): String {
    check(URI(value).scheme == "http" || (!httpOnly && URI(value).scheme == "https")) {
        if (httpOnly) "TARGET_URL_HTTP 必须为 HTTP" else "TARGET_URL 必须为 HTTP 或 HTTPS"
    }
    return value
}
fun main() {
    try {
        val host = env("PROXY_HOST", "t.16yun.cn")!!
        val port = env("PROXY_PORT", "31111")!!.toInt()
        check(port in 1..65535) { "PROXY_PORT 必须为有效端口" }
        val user = env("PROXY_USERNAME", env("PROXY_USER", "user"))!!
        val password = env("PROXY_PASSWORD", env("PROXY_PASS", "password"))!!
        val url = target(env("TARGET_URL", "https://httpbin.org/ip")!!, false)
        val http = target(env("TARGET_URL_HTTP", if (url.startsWith("http://")) url else "http://httpbin.org/ip")!!, true)
        val seed = env("PROXY_TUNNEL", UUID.randomUUID().toString())!!
        fun client() = OkHttpClient.Builder().proxy(Proxy(Proxy.Type.HTTP, InetSocketAddress(host, port)))
            .proxyAuthenticator { _, response ->
                if (response.request.header("Proxy-Authorization") != null) null
                else response.request.newBuilder().header("Proxy-Authorization", Credentials.basic(user, password)).build()
            }.retryOnConnectionFailure(false).connectTimeout(10, TimeUnit.SECONDS)
            .readTimeout(10, TimeUnit.SECONDS).callTimeout(10, TimeUnit.SECONDS).build()
        fun close(client: OkHttpClient) { client.connectionPool.evictAll(); client.dispatcher.executorService.shutdown() }
        fun group(name: String, target: String, reuse: Boolean, tunnel: String?) {
            val shared = if (reuse) client() else null
            try {
                repeat(2) { index ->
                    val current = shared ?: client()
                    try {
                        val request = Request.Builder().url(target).header("Connection", if (reuse) "keep-alive" else "close")
                        if (tunnel != null) request.header("Proxy-Tunnel", tunnel)
                        current.newCall(request.build()).execute().use { response ->
                            check(response.isSuccessful) { "代理请求: HTTP ${response.code}" }
                            println("$name ${index + 1}: ${response.body?.string() ?: ""}")
                        }
                    } finally { if (shared == null) close(current) }
                }
            } finally { if (shared != null) close(shared) }
        }
        group("A 新建连接（重新分配不保证不同 IP）", url, false, null)
        group("B 连接复用", url, true, null)
        group("C-HTTP 同组控制（受出口有效期限制）", http, false, seed)
        println("C-HTTPS 未实现：普通 HTTPS 代理认证不代表支持 CONNECT 自定义头。")
    } catch (failure: Exception) {
        System.err.println(if (failure is IllegalStateException) failure.message else "代理请求失败: ${failure.javaClass.simpleName}")
        kotlin.system.exitProcess(1)
    }
}
