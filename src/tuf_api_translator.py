"""

<Program Name>
 tuf_api_translator.py

<Author>
 Jerry B. Backer

<Started>
 October 26, 2012

<Purpose>
 tuf_api_translator.py takes parameters of low level socket api 
 functions (i.e. socket, connect,send) from the interposition interface (see *****.py), 
 stores information relevant for tuf client, wraps the update request in tuf api for
 download, and returns the status of the update to the software updater.
"""



#imports
#import tuf
#from tuf import updater
from network_call_processor import NetworkCallProcessor
class TUFTranslator(NetworkCallProcessor):
 """
 <Purpose>
  TUFTranslator tracks netwok calls made by the legacy application
  and translate the ones for software updates into TUF api for download.
  The class also sends (simulated) return values of the socket api function
  calls back to the software updater, and returns the contents of the 
  update to the updater.

 <Attributes>
  self.sock_id:
   socket descriptor id 
  self.tuf_client_repo:
   Instance of client repository 
  self.mirror_list:
   mirror list obtained from tuf client repo
  self.network_calls:
   Dictionary containing information (socket number, mirror ip, port, filename)
   of network (socket) calls made by software updater
  self.misc_network_calls:
   Dictionary for network calls made to ip's not in mirror list
   These network calls are forwarded through the translator between software updater and server

 <Methods>
  call_socket():
   When a socket is creation is requested, this function checks the domain family, socket and
   and protocol types. If socket creation is for a network call, socket information is added to 
   update_calls 
   TODO: check process file table (using ulimit) and system descriptor table (how?) for oveflow
   of opened file descriptors 
  call_connect():
    Gets socket id and address. Calls tuf updater to check if address(ip + port) is in mirror list. 
    If address is in mirror list, it is added to dictionary for the socket. Otherwise, 
    socket information is removed from list 
    TODO: redirect non-update connections for processing
  call_send():
    If socket for send request is in update_calls dict, get file information to obtain over network.
    Call TUF API to handle security mechanism for mirror(s) and file requested
  call_recv():
    If call_send was successfull, call_recv wraps targeted file request in TUF API download call. 
    Upon successful download, the function returns the path (or contents) of the downloaded file
    to the network interposition interface, which returns it to the software updater
 call_close():
   upon socket close() call, this function removes the socket from the update_calls dict 
 """
  
 def __init__(self):
	"""
	 <Purpose>
  	   Initiate TUFTranslator that will handle network calls from software updater
	 
	<Arguments>
	   None
	  
	<Return>
	 None
	"""
	#init parent class
	NetworkCallProcessor.__init__(self)		
	
	#socket descriptor id index	
	self.sock_id = 1024
	
	#initialize tuf client
	#self.tuf_client_repo = updater.Repository("tuf_client")
	
	#return mirror list from tuf client repo
	#self.mirror_list = self.tuf_client_repo.get_mirror_list()
		
	# dict of all network calls	
	self.network_calls = {}	
	
	#dict of network calls not made to mirrors
	self.misc_network_calls = {}

 def call_socket(self,domain,socket_type):
	"""
	 <Purpose>
	  Get information about socket request and put socket information in network_calls dict
          If domain is recognized (i.e. AF_INET), return a (simulated) file descriptor id
	  starting from 1025
	  TODO: get max open file size from ulimit and start from there
        <Arguments>
	 domain:
            communication domain which selects the protocol family
	 socket_type:
	    communication semantics
	 protocol:
       <Return>
	 socket file descriptor id	   	
	""" 
	if domain <0:
		print ("Invalid socket domain !")
		return -1 
		#exit("Invalid socket domain !")
	
	self.sock_id+=1
	#add new socket creation request to network call list
	if self.network_calls.get(str(self.sock_id)):
		return -1 
	
	#create dict for socket descriptor id self.sock_id
	str_sock_id = str(self.sock_id)
	self.network_calls[str_sock_id] ={}
	self.network_calls[str_sock_id]['domain'] = domain
	self.network_calls[str_sock_id]['sock_type'] = socket_type
		
	#return (simulated) socket file descriptor id to interposition 
	return self.sock_id
	
	 
 def call_connect(self,sock_descript, ip, port):	
	"""
	  <Purpose>
	   Verify entity at other end of network call. Check if ip is not in mirror lit. 
	   If ip is not in mirror list, add sock_descript to misc_network_calls,create 
	   socket and connect socket to ip and port. The socket obj is saved in misc_network_calls
	   dict with key sock_descript.
	 <Arguments>
	  sock_descript:
	   socket file descriptor id (obtained from call_sock function)
	  ip:
 	   server ip address
	  port:
	   entry port
	
	<Return>
	  if socket was not created or connect() failed for non mirror network call, we return error 
	   message. Otherwise, return 0 
	"""
	str_sock_id = str(sock_descript)
	#socket file descriptor is not in dict
	if not self.network_calls.get(str_sock_id):
		return -1	

 	#if ip_port is in mirror, store mirror info to network_call dict
	"""
	ip_port = str(ip) +':'str(port)
	if self.tuf_client_repo.is_mirror_ip(ip_port):
		self.network_calls[str_sock_id]['ip'] = ip
		self.network_calls[str_sock_id]['port'] = port
		return 0
	else:
		#create socket for non-mirror network access and add to misc_network_calls dict
		#if self.misc_network_calls.get(str_sock_id):
			#return -1 
		#TODO: Handle 2 cases:
			# 1. When socket cannot be created, remove from dict
			# 2. When socket is created, but cannot connect, keep in dict
		try:
			sock_obj = socket.socket(self.network_calls[str_sock_id]['domain'],
					 self.network_calls[str_sock_id]['sock_type'])
			self.misc_network_calls[str_sock_id] = {}
			sock_obj.connect((str(ip),port))	
			self.misc_network_calls[str_sock_id]['sock_obj] = sock_obj
			self.misc_network_calls[str_sock_id]['ip'] = ip
			self.misc_network_calls[str_sock_id]['port'] = port
			return 0
		except socket.error,msg:
			print "Socket Error: " + str(msg[0]) +': '+ msg[1]
			return msg[1] #return error message	
 	"""
 def  call_send(self, sock_descript,msg,flags=0):
	"""
	 <Purpose>
	  If sock_descript is in misc_network_calls dict, get  socket object from misc_network_cals
          dict  and do sock_obj.send(msg,flags). 
	  If not, add msg and flags to network_calls dict for sock_descript
	  Return len(msg) or return value of socket.send() call
	
	<Arguments>
	 sock_descript:
	  socket file descriptor
	 msg:
           string of data to send to socket
	 flags:
           flags for processing and recv
	
        <Return>
	  return value of socket().send() if called or size of msg
	"""
	str_sock_id = str(sock_descript)
	if not self.network_calls.get(str_sock_id):
		return -1
	
	#if socket descriptor is for misc_call, send message
	if self.misc_calls.get(str_sock_id):
		try:
			size = self.misc_calls[str_sock_id]['sock_obj'].send(msg,flags)
			return size
		except socket.error,msg:
			print "Socket creation failed. Error code: " + str(msg[0]) +': '+ msg[1]
			return -1
	#handle mirror requests
	else:
		#parse msg to get file to be updated
		#add file to download to network_calls
		return len(msg)
 def call_recv(self, sock_descript,buff_size,flags=0):
	"""
	 <Purpose>
	  If sock_descript is in misc_network_calls, call misc_network_calls[sock_descript].recv()
	  Otherwise, use tuf security mechanisms to check for mirror and update and upon 
          successful check, download file 
          Return contents of <socket>.recv or downloaded file from tuf

	 <Arguments>
          sock_descript:
	    socket file descriptor
	  buff_size:
            size of buffer for returned data
	  flags:	
	    network flags
	
	<Return>
	 contents of socket.recv() or tuf download mechanism
	"""
	str_sock_id = str(sock_descript)
	if self.misc_calls.get(str_sock_id):
		try:
			recv_buf = self.misc_calls[str_sock_id]["sock_obj"].recv(buff_size,flags)
			return rcv_buf
		except socket.error, msg:
			print "Could not receive from server. Error code: "+ str(msg[0])+': '+msg[1]
			return -1
	else:
		#TODO:call download method from client
		#return downloaded file path/contents
		return 0	

 def call_close(self, sock_descript):
	"""
	 <Purpose>
	  Remove socket with sock_descript id from dictionaries and close its related sockets
	  If sock_descript is in misc_network_calls, call <sock_descript>.close() and remove
         entry with key  sock_descript from misc_network calls. Remove sock_descript from network_calls
	
	<Arguments>
	 sock_descript:
           socket file descriptor
	
	<Return>
         0 if sock_descript was not in misc_network_calls; otherwise, use return value of 
	 <sock_descript>.close() 
	"""
	str_sock_id = str(sock_descript)
	sock_close = 0 
	if self.misc_call.get(str_sock_id):
		try:
			sock_close = self.misc_calls[str_sock_id]["sock_obj"].close()
			del self.misc_call(str_sock_id)
			del self.network_calls(str_sock_id)
		except socket.error, msg:
			print "Coould not close socket. Error code "+str(msg[0]+': '+msg[1]
	else:
		del self.network_calls(str_sock_id)
	
	if len(self.network_calls) == 0:
		self.sock_id = 1024
	
	return sock_close	
