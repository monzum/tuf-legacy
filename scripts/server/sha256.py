import hashlib

#make a hash for a directory
def make_namehash(filename):
  h=hashlib.sha256()
  h.update(filename);
  return h.hexdigest();

#make a hash for a file
def make_filehash(path):

  file_object=open(path, 'rb')
  
  h=hashlib.sha256()
  file_object.seek(0)
  
  while True:
     chunksize=4096
     data = file_object.read(chunksize)
     if not data:
        break
     h.update(data_to_string(data))
     
  file_object.close()
  return h.hexdigest()


def data_to_string(data):
  if isinstance(data, str):
    return data
  elif isinstance(data, unicode):
    return data.encode("utf-8")
  else:
    return str(data)
