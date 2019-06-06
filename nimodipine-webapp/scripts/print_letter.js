"use strict";
var page = require('webpage').create(),
    system = require('system'),
    address, output;

address = system.args[1];
output = system.args[2];
page.viewportSize = { width: 600, height: 600 };
page.paperSize = { format: 'A4', orientation: 'portrait', margin: '1cm' };
page.open(address, function (status) {
  if (status !== 'success') {
    console.log('Unable to load the address!');
    phantom.exit(1);
  } else {
    window.setTimeout(function () {
      page.evaluate(function(s) {
        // force it to fit on A4
        // For DPI discussion, see https://github.com/ebmdatalab/antibiotics-rct/issues/34
        var dpi = 72;
        var body = document.body,
            html = document.documentElement;

        var heightInPix = Math.max( body.scrollHeight, body.offsetHeight,
                                    html.clientHeight, html.scrollHeight, html.offsetHeight );
        var heightInCm = heightInPix * (2.54 / dpi);
        var maxHeight = 27;  // alow for margins
        if (heightInCm > maxHeight) {
          document.body.style.zoom = maxHeight / heightInCm;
        }
        return;
      });
      page.render(output);
      phantom.exit();
    }, 200);
  }
});
