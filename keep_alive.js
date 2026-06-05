const http = require('http');

http.createServer((req, res) => {
  res.write("البوت يعمل 24/7");
  res.end();
}).listen(process.env.PORT || 8080);

console.log("نظام Keep Alive يعمل بنجاح!");
