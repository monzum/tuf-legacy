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


import os
import sys
import socket

#sys.path.append("TUF/src/")
#import example_client
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
  is_mirror():
   Return 1 if a socket is opened for a TUF mirror. Otherwise, return 0
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
  
 def __init__(self, server_ip):
    """
     <Purpose>
       Initiate TUFTranslator that will handle network calls from software updater
     <Arguments>
	server_ip:
	  ip address of updater server 
     <Return>
	None
    """
 		
    #init parent class
    NetworkCallProcessor.__init__(self)		
	
    #socket descriptor id index	
    self.sock_id = 1024
	
    self.server_ip = server_ip
	
    #get mirror list dict from Konstantin's module
    #self.mirror_list = example_client.get_mirrors()	
    self.mirror_list = {}
   
    # dict of all network calls	
    self.network_calls = {}	
	
    #dict of network calls not made to mirrors
    self.misc_network_calls = {}

 def is_mirror(self,ip):
    """
      <Purpose>
        Check if ip is in mirror list dict
      <Arguments>
	ip_port:
	   ip: ip of connect() parameter
      <Return>
	 0 if mirror is not in list, 1 if it is
    """
    for mirror_name in self.mirror_list:
      mirror_url = self.mirror_list[mirror_name]['url_prefix']
      mirror_ip = socket.gethostbyname(mirror_url)
      if mirror_ip == ip:
        return 1
      return 0
	
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
      <Return> 
        (socket_descript_id, -1) on success
	(None, socket_errno) on failure	   	
	""" 
    if domain <0:
      return (None, 97)
    if socket_type <0: 
      return (None, 22)
				
    self.sock_id+=1

    if self.network_calls.get(str(self.sock_id)):
      return (None, 13) 
	
    #create dict for socket descriptor id self.sock_id
    str_sock_id = str(self.sock_id)
    self.network_calls[str_sock_id] ={}
    self.network_calls[str_sock_id]['domain'] = int(domain)
    self.network_calls[str_sock_id]['sock_type'] = int(socket_type)
	
    #return (simulated) socket file descriptor id to interposition 
    return (self.sock_id,-1)
	
	 
 def call_connect(self,sock_descript, addr, port):	 
    """
      <Purpose>
        Verify entity at other end of network call. Check if ip is not in mirror lit. 
	If ip is not in mirror list, add sock_descript to misc_network_calls,create 
	socket and connect socket to ip and port. The socket obj is saved in misc_network_calls
	dict with key sock_descript.
      <Arguments>
	sock_descript:
	  socket file descriptor id (obtained from call_sock function)
	addr:
 	  server ip address 
	port:
	 entry port
	
      <Return>
        (0, -1) on success
	(None, socket_errno) on failure
    """
    str_sock_id = str(sock_descript)
    #socket file descriptor is not in dict
    if not self.network_calls.get(str_sock_id):
      return (None,9)	
	
    ai_addr = addr + ':'+str(port)
	
    #check mirror list for ai_addr
    #self.mirror_list = tuf.Konst.get_mirror_list()
    mirror = self.is_mirror(addr)
	
    if mirror:	
      self.network_calls[str_sock_id]['addr'] = addr
      self.network_calls[str_sock_id]['port'] = int(port)
      return (0,-1)
    else:
			
      try:
        sock_obj = socket.socket(
		self.network_calls[str_sock_id]['domain'],
		self.network_calls[str_sock_id]['sock_type'])
	self.misc_network_calls[str_sock_id] = {}
	sock_obj.connect((addr,int(port)))	
	
	#adding connect parameters to dict 
	self.misc_network_calls[str_sock_id]['sock_obj'] = sock_obj
	self.misc_network_calls[str_sock_id]['addr'] = addr
	self.misc_network_calls[str_sock_id]['port'] = int(port)
			
	#if ip is of server, update
	# call Konstatntin's update function			
	# can server also work as mirror? if so, put this outside
        if addr == self.server_ip:
	  print("try and except konstantin's update_mirror func")	
	  return (0,-1)
      except socket.error,msg:
        return (None, msg[0])
	
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
	(len(msg, -1) on success
	 (None, errno) on failure 
    """
    str_sock_id = str(sock_descript)
    if not self.network_calls.get(str_sock_id):
      return (None, 9)
	
    #if socket descriptor is for misc_call, send message
    if self.misc_network_calls.get(str_sock_id):
      try:
        size = self.misc_network_calls[str_sock_id]['sock_obj'].send(msg,int(flags))
	return (size, -1)
      except socket.error,msg:
        return (None, msg[0])
    else:
      #split request into its components
      #[method][request-uri][protocol]
      request_components = msg.split()
      if len(request_components[1]) == 0 or len(request_components[1]) == '/':
        return (None,22) 
      self.network_calls[str_sock_id]['update_file']=request_components[1]	
      return (len(msg),-1)


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
    if not self.network_calls.get(str_sock_id):
      return (None, 9)
	
    if self.misc_network_calls.get(str_sock_id):
      try:
        recv_buf = self.misc_network_calls[str_sock_id]["sock_obj"].recv(int(buff_size),int(flags))
	return (recv_buf,-1)
      except socket.error, msg:
        return (None, msg[0])
			
    else:
      print ("Try/Except konstantin's update targets function")	
      #return (filecontents,-1) or (None, error_msg)
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
       	(0,-1) if socket was sucesfully close (None, errno) otherwise
    """
    str_sock_id = str(sock_descript)
    sock_close = -1 
	
    if not self.network_calls.get(str_sock_id):
      return (None, 9)

    if self.misc_network_calls.get(str_sock_id):
      try:
        sock_close = self.misc_network_calls[str_sock_id]["sock_obj"].close()
	del self.misc_network_calls[str_sock_id]
	del self.network_calls[str_sock_id]
      except socket.error, msg:
	return (None, sock_close)
    else:
      del self.network_calls[str_sock_id]
	
    if len(self.network_calls) == 0 and len(self.misc_network_calls) == 0:
      self.sock_id = 1024

   return (0,-1)		


"""
#small testing stuff
def main():
	testing = TUFTranslator("127.1.100")
	ret = testing.call_socket(socket.AF_INET,socket.SOCK_STREAM)
	ret2 = testing.call_connect(ret[0],"www.google.com",80)
#	ret3 = testing.call_send(ret[0],"Hello")
#	ret4 = testing.call_recv(ret[0],1024)
	
	print ret2
if __name__ == "__main__":
	main()
"""
