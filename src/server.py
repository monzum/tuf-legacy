"""
<Program Name>
  server.py

<Purpose>
  Launches a SimpleHTTPServer that serves files inthe current directory.

<Author>
  Konstantin Andrianov

"""

import SimpleHTTPServer
import SocketServer

PORT = 8101

Handler = SimpleHTTPServer.SimpleHTTPRequestHandler

httpd = SocketServer.TCPServer(("", PORT), Handler)

print "Serving at port: "+str(PORT)
httpd.serve_forever()

