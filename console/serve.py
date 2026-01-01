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

http_server = HTTPServer(app)
http_server.listen(8080, address="0.0.0.0")

print("HTTPS livereload running on https://192.168.2.109:8080")
IOLoop.current().start()
