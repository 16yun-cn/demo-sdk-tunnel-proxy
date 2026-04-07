var system = require('system');
var target = system.args[1] || 'http://httpbin.org/ip';
var tunnelSeed = system.args[2] || 'nodejs-phantomjs-demo';
var page = require('webpage').create();
page.settings.userAgent = 'Mozilla/5.0';
page.customHeaders = { 'Proxy-Tunnel': tunnelSeed };

page.open(target, function(status) {
  console.log('status>', status);
  console.log(page.content);
  phantom.exit();
});
