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
import threading
import traceback


# Define some global values and errorcodes.
ECONNRESET = 104
EBADF = 9


class LibnitListener():
  # LibnitListener is a module that is used to listen and process
  # network calls that is forwarded by libnit which is interposing
  # on network calls on an application.


  def __init__(self, network_call_processor, libnit_port = 53678, debug_mode=False):
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
    self.debug_mode = debug_mode



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

    while True:
      (libnit_conn, libnit_addr) = libnit_sock.accept()
  
      # Once we have accepted the connection, launch a new thread to handle
      # the new connection.
      network_handle_thread = threading.Thread(target=self.handle_network_requests, args=(libnit_conn,))
      network_handle_thread.start()
    



  def handle_network_requests(self, libnit_conn):
    """
    <Purpose>
      Given a socket connection, handle all the network requests
      made on that particular socket.

    <Arguments>
      libnit_conn - the connection to handle.

    <Exception>
      No exceptions are raised, however if libnit_conn closes then
      this function exits.

    <Return>
      None
    """
    # Continuously serve all the incoming network call requests.
    # POSSIBLE BUG: I return from this function when libnit_conn
    # raises an error on recv or send. Hopefully if the application
    # closes then a socket.error would be raised. However if no error
    # is raised when the application closes, then this thread may run
    # forever.
    while True:
      # Receive the incoming request.
      try:
        request = libnit_conn.recv(4096)
      except:
        if self.debug_mode:
          print "Connection has been closed on: " + str(libnit_conn)
        return

      if not request:
        continue

      if self.debug_mode:
        print "Received request: '%s'" % request

      # Unwrap the request that the application made.
      network_call_type, call_args = self.deserialize_network_call(request)
    
      try:
        return_response, return_err = self.make_network_request(network_call_type, call_args)
      except Exception, err:
        if self.debug_mode:
          print "Got a bad error: " + str(traceback.format_exc())

        # If there is any error at all then we just send back
        # the ECONNRESET errorcode.
        return_response = ""
        return_err = ECONNRESET
        
      # Now that we have processed the network call, we are going to serialize
      # the response and error codes from the call then return it back to libnit.
      serialized_response = self.serialize_network_call_response(return_response, return_err)

      if self.debug_mode:
        print "Returning response: " + serialized_response

      try:
        bytes_sent = libnit_conn.send(serialized_response)
      except:
        if self.debug_mode:
          print "Connection has been closed on: " + str(libnit_conn)
        return
  



  def serialize_network_call_response(self, return_response, return_err):
    """
    <Purpose>
      In order to return the response and the error codes of the network
      call to Libnit, we will serialize the respone and error code into
      a string.

    <Arguments>
      return_response - The response from the call.

      return_err - The error code to return if there was any.

    <Return>
      A serialized string with the network call's response and error.
    """
    if return_response == None:
      return_val = "-1"
    else:
      return_val = str(return_response)

    print "Return response is: " + str(return_response) + "Return val is: " + str(return_val)
    print "Packing values:", return_val, return_err

    struct_format = "<i%ds" % len(return_val)
    print type(return_err), type(return_val)
    packed_msg = struct.pack(struct_format, return_err, return_val)

    return packed_msg






  def deserialize_network_call(self, request):
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
    arg_len = len(request) - 19

    # Unpack the received message into the function call and arg list.
    print len(request)
    unpack_list = struct.unpack("19s%ds" % arg_len, request)

    # Since the data sent from the C side will have lots
    # of garbage (mostly null characters) after the actual data,
    # we clean up unpacked data.
    call_func = unpack_list[0].strip('\0')
    call_args = unpack_list[1].strip('\0')
    
    return (call_func, call_args)





  def make_network_request(self, call_name, call_args):
    """
    <Purpose>
      Given a network call name and arguments. Process the
      call with the arguments.

    <Arguments>
      call_name - The network call we need to make.

      call_args - A list of all the arguments.

    <Return>
      A tuple with the error code and response.
    """

    # Retrieve the process function that will be used to process
    # the network call.
    process_method_name = "call_" + call_name

    process_method = getattr(self.network_call_processor, process_method_name)

    # Split the arguments.
    call_arg_list = call_args.split(',')

    try:
      # Process the 'socket' call.
      if call_name == 'socket':
        domain = call_arg_list[0]
        socket_type = call_arg_list[1]
        
        return process_method(domain, socket_type)

      # Process the 'connect' call.
      elif call_name == 'connect':
        sock_fd = call_arg_list[0]
        conn_ip = call_arg_list[1]
        conn_port = call_arg_list[2]

        return process_method(sock_fd, conn_ip, conn_port)

      # Process the 'send' call.
      elif call_name == 'send':
        # Split the arguments a little differently. The message in send might
        # have the character ','. So we split it only twice.
        call_arg_list = call_args.split(',', 2)

        sock_fd = call_arg_list[0]
        flags = call_arg_list[1]
        msg_to_send = call_arg_list[2]
        
        return process_method(sock_fd, msg_to_send, flags)
      
      # Process the 'recv' call.
      elif call_name == 'recv':
        sock_fd = call_arg_list[0]
        len_to_recv = call_arg_list[1]
        flags = call_arg_list[2]
      
        return process_method(sock_fd, len_to_recv, flags)

      
      # Process the 'close' call.
      elif call_name == 'close':
        sock_fd = call_arg_list[0]

        return process_method(sock_fd)
    except Exception, err:
      if self.debug_mode:
        print "Got a bad error: " + str(traceback.format_exc())
          
      return (0, ECONNRESET)


    
# ===========================================================================
# Define Exceptions
# ===========================================================================
class InvalidNetworkCall(Exception):
  """
  This error is raised if an invalid network call is made. Raised
  if we are unable to deserialize the network call made by libnit.
  """
  pass
