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

class TUFTranslator(object):
 """
 <Purpose>
  TUFTranslator tracks netwok calls made by the legacy application
  and translate the ones for software updates into TUF api for download.
  The class also sends (simulated) return values of the socket api function
  calls back to the software updater, and returns the contents of the 
  update to the updater.

 <Attributes>
  self.update_calls:
   Dictionary containing information (socket number, mirror ip, port, filename)
   of file update request
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
