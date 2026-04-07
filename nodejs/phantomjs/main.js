const { spawn } = require('child_process');
const path = require('path');

const host = process.env.PROXY_HOST || '127.0.0.1';
const port = process.env.PROXY_PORT || '31111';
const user = process.env.PROXY_USERNAME || process.env.PROXY_USER || 'user';
const pass = process.env.PROXY_PASSWORD || process.env.PROXY_PASS || 'password';
const target = process.env.TARGET_URL || 'http://httpbin.org/ip';
const tunnelSeed = process.env.PROXY_TUNNEL || process.env.TUNNEL_SEED || 'nodejs-phantomjs-demo';

const phantomBin = path.join(__dirname, 'node_modules', '.bin', 'phantomjs');
const script = path.join(__dirname, 'http-demo.js');
const args = [
  `--proxy=${host}:${port}`,
  `--proxy-auth=${user}:${pass}`,
  script,
  target,
  tunnelSeed,
];

const child = spawn(phantomBin, args, {
  cwd: __dirname,
  stdio: 'inherit',
  env: process.env,
});

child.on('exit', (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 1);
});
