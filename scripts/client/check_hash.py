import csv


#return dict of manifest
def read_manifest(path):
  #read the file
  reader=csv.reader(open(path))
  entries=[]

  #for each line in the reader object
  #append a list of the items i.e. [filename, hash, length]
  #to the list of entries
  for row in reader:
    entries.append(row[0].split())
  entries_dict = {}
  for e in range(0, len(entries)):
    entries_dict[entries[e][0]]=entries[e][1:] 
 
  return entries_dict

def check_hashes(my_manifest, check_manifest):
  my_hashes_dict=read_manifest(my_manifest)
  check_hashes_dict=read_manifest(check_manifest)

   #Check what has changed on the server
  diff = set() #empty set
  for key in check_hashes_dict:
    if key not in my_hashes_dict:
      diff.add(key) 
    else:
      if my_hashes_dict[key] != check_hashes_dict[key]:
        diff.add(key)

  #diff=set(check_hashes_dict.keys()) - set(my_hashes_dict.keys()) 

  #print diff
  return diff

#check_hashes(r'MANIFEST', r'MANIFEST_temp')
