import csv

def read_manifest(path):
  #read the file
  reader=csv.reader(open(path))
  entries=[]

  #for each line in the reader object
  #append a list of the items i.e. [filename, hash, length]
  #to the list of entries
  for row in reader:
    entries.append(row[0].split())
  return entries

def check_hashes(my_manifest, check_manifest):
  my_hashes=read_manifest(my_manifest)
  check_hashes=read_manifest(check_manifest)

  
  my_hashes_dict={}
  check_hashes_dict={}
  for e in range(0, len(my_hashes)):
    my_hashes_dict[my_hashes[e][0]]=my_hashes[e][1:]
  for j in range(0, len(check_hashes)):
    check_hashes_dict[check_hashes[j][0]]=check_hashes[j][1:]

  #Check what has changed on the server
  diff=set(check_hashes_dict.keys()) - set(my_hashes_dict.keys()) 

  print diff
  return diff

check_hashes(r'MANIFEST', r'MANIFEST_temp')
