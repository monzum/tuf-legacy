import httplib
import sys
#from check_hash import *

def get_NETWORK_FILE(http_server,file_path):
   manifest = open("MANIFEST", 'wb') 
   conn=httplib.HTTPConnection(http_server)	
   conn.request("GET", file_path) 
   rsp = conn.getresponse()
   data_received=rsp.read()
   #manifest.write(data_received)
   conn.close()
   return data_received

#get_MANIFEST("http://localhost:8101")
#check_hashes("MANIFEST_temp", "MANIFEST")


