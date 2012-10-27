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
  module that defines how to handle the network calls. 

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
    ...
    ...
    # Stop LibnitListener from serving any further network calls.
    interpose_listener.stop_serving()


<History>
  10/27/2012 - First implementation of LibnitListener.
"""


class 

