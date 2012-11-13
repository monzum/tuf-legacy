from get_manifest import *
from check_hash import *

get_MANIFEST(sys.argv[1])
if check_hashes("MANIFEST", "MANIFEST_temp"):
  manifest = open("MANIFEST", 'wb')
  temp = open("MANIFEST_temp", 'rb')
  new_man = temp.read()
  manifest.write(new_man)
  
