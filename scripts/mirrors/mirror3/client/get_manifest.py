import httplib
import sys
#from check_hash import *

http_server= sys.argv[1]

def get_MANIFEST(http_server):
   manifest = open("MANIFEST_temp", 'wb')
   conn=httplib.HTTPConnection(http_server)

   conn.request("GET", "/MANIFEST")
   rsp = conn.getresponse()
     
   data_received=rsp.read()
   manifest.write(data_received)
   conn.close()


get_MANIFEST(http_server)
#check_hashes("MANIFEST_temp", "MANIFEST")


