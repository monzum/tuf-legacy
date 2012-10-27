"""
<Program Name>
  libnit_listener.py

<Author>
  Monzur Muhammad
  mmuham01@students.poly.edu

<Date Started>
  October 27th, 2012

<Purpose>
  The LibnitListener is a module that is used to listen for a connection
  from the Libnit library and process all incoming connection. Libnit
  interposes on all the network calls from an application and forwards
  all the arguments for the call. LibnitListener launches a server that
  waits for all the network call traffic sent from Libnit and unpacks
  the argument. After unpacking the arguments, it calls the appropriate
  function in order to process a particular network call. In order to use
  LibnitListener, it must first be initialized with a network call processor
  module that defines how to handle the network calls. Look at 
  network_call_processor.NetworkCallProcessor to see how to define the
  processor module.

  The following function calls should be defined in the processor module:
    * call_socket()
    * call_connect()
    * call_listen()
    * call_accept()
    * call_bind()
    * call_send()
    * call_recv()
    * call_sendto()
    * call_recvfrom()
    * call_select()
    * call_getsockopt()
    * call_setsockopt()
    * call_close()


<Usage>
  This is the simple way of using the LibnitListener library.

    # Create processor function instance.
    sample_process_mod = SampleProcessFunction()

    # Initialize LibnitListener with a sample network processor function.
    # Then launch the listener to serve forever.
    interpose_listener = LibnitListener(sample_process_func)
    interpose_listener.serve_forever()


<History>
  10/27/2012 - First implementation of LibnitListener.
"""


import socket
import struct


class LibnitListener():
  # LibnitListener is a module that is used to listen and process
  # network calls that is forwarded by libnit which is interposing
  # on network calls on an application.


  def __init__(self, network_call_processor, libnit_port = 53678):
    """
    <Purpose>
      Initialize LibnitListener with a network call processor.

    <Arguments>
      network_call_processsor - A processor function that can 
        be used to process network calls. Take a look at the 
        NetworkCallProcessor class to understand
        which calls need to be defined.
  
    <Exceptions>
      None

    <Return>
      None
    """

    # Use the provided object to process all network calls.
    self.network_call_processor = network_call_processor
    self.libnit_port = libnit_port






  def serve_forever(self):
    """
    <Purpose>
      Listen for incoming connection from Libnit and process all
      incoming network connections appropriately with the provided
      network processor object.

    <Arguments>
      None

    <Exceptions>
      Exceptions may be raised if we crash unexpectedly. 

    <Return>
      None
    """

    # Create a new listening socket and wait for an incoming connection 
    # from Libnit. Once the connection has been established, we serve
    # all the network requests that Libnit makes.
    libnit_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    libnit_sock.bind(('127.0.0.1', self.libnit_port))
    libnit_sock.listen(1)

    print "Starting to listen on port '%d' for Libnit connections." % self.libnit_port
    libnit_conn = libnit_sock.accept()
    
    
    # Continuously serve all the incoming network call requests.
    while True:
      # Receive the incoming request.
      request = libnit_conn.recv(4096)

      print "Received request: '%s'" % request
      # Unwrap the request that the application made.
      network_call_type, call_args = self.deserialize_network_call(request)
      print network_call_type, call_args





  def deserialize_network_call(request):
    """
    <Purpose>
      The purpose is to deserialize the network call made that 
      is sent over from libnit using struct.

    <Arguments>
      request - a string that contains the serialized form of
        the network request.

    <Exception>
      InvalidNetworkCall is raised if we are unable to properly
      deserialize the network call.

    <Return>
      Returns a tuple of network call name and a list of arguments
      for the network call.
    """

    # The first 20 bytes is used to store the network call name.
    arg_len = len(request) - 21

    # Unpack the received message into the function call and arg list.
    unpack_list = struct.unpack("19s%ds" % arg_len, request)

    # Since the data sent from the C side will have lots
    # of garbage (mostly null characters) after the actual data,
    # we clean up unpacked data.
    call_func = list_recv[0].strip('\0')
    call_args = list_recv[1].strip('\0')
    
    return (call_func, call_args)





  def make_network_request(self, call_name, call_args):
    pass



       
  







# ===========================================================================
# Define Exceptions
# ===========================================================================
class InvalidNetworkCall(Exception):
  """
  This error is raised if an invalid network call is made. Raised
  if we are unable to deserialize the network call made by libnit.
  """
  pass
