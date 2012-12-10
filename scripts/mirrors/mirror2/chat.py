import socket
import time
import hashlib
import shutil
import csv
import urllib

# generate md5 of manifest file
def manifestfile(path):

	manifest = open(path,'rb')

	m = hashlib.md5()

	content = manifest.read()

	# if content is null, return None
	if not content:
		return None

	m.update(content)

	manifest.close()

	return m.hexdigest()



# return dict of manifest
def read_manifest(path):
	#read the file
	reader=csv.reader(open(path))
	entries=[]
	entries_dict = {}
	#for each line in the reader object
	#append a list of the items i.e. [filename, hash, length]
	#to the list of entries
	try:
		for row in reader:
			entries.append(row[0].split())
	except:
		pass

	for e in range(0, len(entries)):
		entries_dict[entries[e][0]]=entries[e][1:] 

	return entries_dict


# compare mirror's manifest and new manifest file from server, find difference and return it
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

  #print diff
  return diff



# current datetime
def now():
	return time.strftime('%m-%d-%Y %H:%M:%S',time.localtime(time.time()))



if __name__ == '__main__':
	i=0

	while True:
		i=i+1
		print i

		# initial socket
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		print now()+':socket initial'

		# connect to server
		sock.connect(('localhost', 8102))
		print now()+':socket connected'

		# tell server which mirror it is 
		sock.send('mirror1')

		# generate md5
		checkvalue = manifestfile('./MANIFEST')
		print now()+':compute file md5'
		print checkvalue

		time.sleep(5)
		print now()+':sleep 5 seconds'

		# receive md5 from server
		recvd = sock.recv(1024)
		print recvd

		# compare mirror manifest md5 and server manifest md5, if they dont match,
		# call copy() function, and download new manifest from server,
		# compare mirror manifest and server manifest.
		# download updates from server
		if checkvalue != recvd:

			print now()+':server manifest has been changed'

			shutil.copyfile('./MANIFEST','./mirror_manifest')

			# download new manifest from server,
			urllib.urlretrieve ("http://localhost:8101/MANIFEST", "./MANIFEST")

			# compare mirror manifest and server manifest, return dif set()
			dif = check_hashes('./mirror_manifest','./MANIFEST')
			# download updates from server
			for x in dif:
				basename = x.split('/')
				basename = basename[len(basename)-1]
				
				urllib.urlretrieve ("http://localhost:8101/" + x, "./files/" + basename)
			print "update to the date"
			#TODO : HAVE mirrors updating TUF-related metadata and files
		sock.close()
