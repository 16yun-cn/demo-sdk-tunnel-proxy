var system = require('system');
var target = system.args[4] || 'http://httpbin.org/ip';
var tunnelSeed = system.args[5] || 'nodejs-casperjs-demo';
var casper = require('casper').create();

casper.on('started', function () {
  this.page.customHeaders = {
    'User-Agent': 'Mozilla/5.0',
    'Proxy-Tunnel': tunnelSeed
  };
});

casper.start(target);
casper.then(function() {
  this.echo(this.getPageContent());
});
casper.run();
