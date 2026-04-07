using System;
using System.IO;
using System.Net;
using System.Text;

class Program {
  static string BuildProxyAuthorization(string user, string pass) {
    return "Basic " + Convert.ToBase64String(Encoding.UTF8.GetBytes($"{user}:{pass}"));
  }

  static void Main() {
    string host = Environment.GetEnvironmentVariable("PROXY_HOST") ?? "t.16yun.cn";
    string port = Environment.GetEnvironmentVariable("PROXY_PORT") ?? "31111";
    string user = Environment.GetEnvironmentVariable("PROXY_USERNAME") ?? "user";
    string pass = Environment.GetEnvironmentVariable("PROXY_PASSWORD") ?? "password";
    string target = Environment.GetEnvironmentVariable("TARGET_URL") ?? "http://httpbin.org/ip";
    string seed = Environment.GetEnvironmentVariable("TUNNEL_SEED") ?? "1";

    var credentials = new NetworkCredential(user, pass);
    var encodedUser = Uri.EscapeDataString(user);
    var encodedPass = Uri.EscapeDataString(pass);
    var proxy = new WebProxy($"http://{encodedUser}:{encodedPass}@{host}:{port}", true) {
      Credentials = credentials
    };
    var req = (HttpWebRequest)WebRequest.Create(target);
    req.Method = "GET";
    req.Proxy = proxy;
    req.PreAuthenticate = true;
    req.Headers.Add("Proxy-Authorization", BuildProxyAuthorization(user, pass));
    req.Headers.Add("Proxy-Tunnel", seed);
    using var resp = (HttpWebResponse)req.GetResponse();
    using var sr = new StreamReader(resp.GetResponseStream()!, Encoding.UTF8);
    Console.WriteLine((int)resp.StatusCode);
    Console.WriteLine(sr.ReadToEnd());
  }
}
