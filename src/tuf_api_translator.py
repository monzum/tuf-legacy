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
import tuf
from tuf import updater
from network_call_procesor import NetworkCallProcessor
class TUFTranslator(NetworkCallProcessor):
 """
 <Purpose>
  TUFTranslator tracks netwok calls made by the legacy application
  and translate the ones for software updates into TUF api for download.
  The class also sends (simulated) return values of the socket api function
  calls back to the software updater, and returns the contents of the 
  update to the updater.

 <Attributes>
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
	#initialize tuf client
  	self.tuf_client_repo = updater.Repository("tuf_client")
	
	#return mirror list from tuf client repo
	self.mirror_list = self.tuf_client_repo.get_mirror_list()
		
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
            communication domain which selects the protocol famil
	 socket_type:
	    communication smeantics
	 protocol:
       <Return>
	 socket file descriptor id	   	
	""" 

 
  def call_connect(self,sock_descript, ip, port):	
	"""
	  <Purpose>
	   Verify entity at other end of network call. Check if ip is not in mirror lit. 
	   If ip is not in mirror list, add sock_descript to misc_network_calls,create 
	   socket and connect socket to ip and port. The socket obj is saved in misc_network_calls
	   dict with key sock_descript.
	   Either way, netowrk_calls dict is updated for sock_descript entry
	 <Arguments>
	  sock_descript:
	   socket file descriptor id (obtained from call_sock function)
	  ip:
 	   server ip address
	  port:
	   entry port
	
	<Return>
	  if socket was not created or connect() failed for non mirror network call, we return -1
	  otherwise, return 0 
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
