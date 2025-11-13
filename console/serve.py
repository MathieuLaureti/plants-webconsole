import ssl
from livereload import Server
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application, StaticFileHandler

# serve current directory
app = Application([
    (r"/(.*)", StaticFileHandler, {"path": ".", "default_filename": "index.html"}),
])

# livereload setup
server = Server(app)
server.watch("*.html")
server.watch("*.js")
server.watch("*.css")

# SSL setup
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(
    certfile="/home/mlaureti/plant_webconsole/certs/192.168.2.109.pem",
    keyfile="/home/mlaureti/plant_webconsole/certs/192.168.2.109-key.pem",
)

# run with HTTPS
http_server = HTTPServer(app, ssl_options=context)
http_server.listen(8080, address="0.0.0.0")

print("HTTPS livereload running on https://192.168.2.109:8080")
IOLoop.current().start()
