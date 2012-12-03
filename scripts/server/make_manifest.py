import os, os.path
from sha256 import make_namehash, make_filehash

#Creates a Manifest file in the form
# < file/dir name> <hash> <length>
#of all files and directories being served

def make_manifest():
  manifest = open("MANIFEST", 'wb')
  for dirname, dirnames, filenames in os.walk('legacy-app-lib'):
    print filenames
    #add a manifest entry for a sub-directory
    for subdirname in dirnames:
      tmp = os.path.join(dirname, subdirname)
      h = make_namehash(tmp);
      len = os.path.getsize(tmp)
      print (tmp+" "+str(len))
      manifest.write(tmp+" "+str(h)+" "+str(len)+'\n')
    #add a manifest entry for a file
    for filename in filenames:
      tmp = os.path.join(dirname, filename)
      h = make_filehash(tmp);
      len = os.path.getsize(tmp)
      print (tmp+" "+str(len)) 
      manifest.write(tmp+" "+str(h)+" "+str(len)+'\n')
    
make_manifest()
