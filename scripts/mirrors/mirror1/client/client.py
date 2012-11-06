import httplib
import sys

http_server= sys.argv[1]

def get_MANIFEST(http_server):
   manifest = open("MANIFEST", 'wb')
   conn=httplib.HTTPConnection(http_server)

   while 1:
     conn.request("GET", "/MANIFEST")
     rsp = conn.getresponse()
     
     #print(rsp.status, rsp.reason)
     data_received=rsp.read()
     manifest.write(data_received)
   conn.close()


get_MANIFEST(http_server)
