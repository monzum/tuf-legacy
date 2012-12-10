#11/21/2012
#legacy-client application
"""
 <Purpose>
   Legacy application with built-in software updater
   Application does:
		- call built-in software updater for updates
		- does its regular work (contact google server)
		- quit  
   Built in software updater does the following:
	- get manifest from server
	- compare hashes of new manifest and old
	- download files that need to be updated

legacy-client application options:
	u: perform software update ->uses built-in software updater
	w: perform regular work (sample work is connect and send of msg to google server)
	q: quit client application
		
"""
import errno
import socket
import sys
import os
import urllib
import httplib
import sys
from check_hash import *
from random import choice


#server and mirrors are hardcoded
SERVER_ADDRESS = "127.0.0.1:8101"
MIRRORS = ["127.0.0.1:8000", "127.0.0.1:8001","127.0.0.1:8002"]
  



#basic method that gets contents of file from server or mirrors
def get_file_from_network(url,file_path):
        try: 
	   conn=httplib.HTTPConnection(url) 
   	   conn.request("GET", file_path)  
	   rsp = conn.getresponse()
  
   	   data_received=rsp.read()
   	   conn.close()
   	   return data_received
	except:
	  return None


#built-in software updater
def perform_update():
	manifest_contents = get_file_from_network(SERVER_ADDRESS,"/MANIFEST")
	if manifest_contents is None:
	  print "Error getting MANIFEST from server"
	  return None
	manifest = open("MANIFEST_temp", 'wb') 
  	manifest.write(manifest_contents )
  	manifest.close() 
        	
	#perform hash comparison
	hash_diff = check_hashes(r'MANIFEST', r'MANIFEST_temp')
	if hash_diff: #update manifest file
          to_update =  read_manifest("MANIFEST")
	  new_manifest = read_manifest("MANIFEST_temp") 
	
	  # perform update on files all files that are out of date   
	  for file_to_update in hash_diff:
	    file_basename = os.path.basename(file_to_update)
	    print "Updating "+ file_basename+ "\n"
            try: 
	      file_contents= get_file_from_mirror(file_basename)     
              
	      #update files locally
	      print "File "+ file_basename +" updated\n"
	      file_handle = open(file_basename ,"w")
              file_handle.write(file_contents)
	      file_handle.close()	         
	      
	      to_update[file_to_update] = new_manifest[file_to_update]
	    except:
	      print "Could  not update file: "+ file_basename 

	   #update local manifest
	  handle = open("MANIFEST","w")   
	  for key in to_update:
            handle.write(str(key)+" "+to_update[key][0]+ " "+to_update[key][1]+"\n")
	  handle.close()
	else: # no hash difference
	  print "All files are up to date"
	
	os.remove(os.path.abspath("MANIFEST_temp")) 
  

#use mirrors to download files
#TODO: Mechanism for mirror to sync file with server (tried rsync and PUT request.. none worked)
def get_file_from_mirror(file_to_update):
       

  #mirrorlist = MIRRORS 12/06/2012. Bug found by David. Contents of MIRRORS are removed
  mirrorlist =["127.0.0.1:8000", "127.0.0.1:8001","127.0.0.1:8002"]
  
  
  while(True): 
    if len(mirrorlist) == 0: 
      raise errno.ENOENT #imitate file not found. should do custom error for "out of mirrors" 
    mirror = choice(mirrorlist)
    mirrorlist.remove(mirror)
    (ip, port) = mirror.split(':') 
    #perform file update
    try: 
      s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
      s.connect((ip,int(port))) 
      s.send("GET " + str(file_to_update) + " HTTP/0.9\n\n",0)
      update = s.recv(8192)
      s.close()
    except: 
      continue #go onto the next IP 
    return update
               

#Purpose: simulate regular (network) work being done by legacy application
def legacy_work():
	try:
	        sock =socket.socket(socket.AF_INET,socket.SOCK_STREAM)	
		sock.connect(('173.194.75.99',80))
		sock.send("GET /index.html  HTTP/1.1\r\n\r\n")	
		sock.recv(1024)
		sock.close()
		print "success"
	except:
		print "error in doing work of legacy application"


#Purpose: quit application
def quit_application():
	sys.exit(0)
	

def main():

	print("Welcome to the legacy-app\nOptions:")
	print("u: check server for updates and perform upddate")
	print("w: perform regular work of legacy application")
	print("q: quit the legacy application\n")
	        
        while(True):
		print("\nWhat would you like to do ?(u,w or q)")
		try:
			op = str(raw_input())
			 
			if op == 'u':
				perform_update()
			elif op == 'q':
				quit_application()
			elif op == 'w':
				legacy_work()
			else:
				print "Invalid options type"
		except ValueError:
			print "Invalid option type"
 
if __name__ == "__main__":
	main() 
