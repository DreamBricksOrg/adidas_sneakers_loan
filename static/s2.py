
# taken from http://www.piware.de/2011/01/creating-an-https-server-in-python/
# generate server.pem with the following command:
#    openssl req -new -x509 -keyout key.pem -out server.pem -days 365 -nodes
# run as follows:
#    python simple-https-server.py
# then in your browser, visit:
#    https://localhost:4443

from http.server import HTTPServer, BaseHTTPRequestHandler
import http.server
import ssl


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        #self.wfile.write(b'Hello, world!')
        with open("test_qrcode2.html", mode="rb") as html_file:
            htmlcode = html_file.read()
            self.wfile.write(htmlcode)
            return
        self.wfile.write(b"error")
    
    
server_address = ('192.168.15.163', 4443)
httpd = http.server.HTTPServer(server_address, SimpleHTTPRequestHandler)
httpd.socket = ssl.wrap_socket(httpd.socket,
                               server_side=True,
                               keyfile="privateKey.key",
                               certfile="certificate.crt")
httpd.serve_forever()