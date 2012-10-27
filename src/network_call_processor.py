"""
<Library Name>
  NetworkCallProcessor - This library defines the base
    network calls that need to be defined.

<Author>
  Monzur Muhammad

<Date Started>
  October 27th, 2012

<Usage>
  This is just a base framework, to use the NetworkCallProcess
  you will need to inherit this class and overload each of the
  functions.

  Example:
    from network_call_processor import NetworkCallProcessor
  
    class ProcessSimpleCall(NetworkCallProcessor):
    
      def __init__(self):
        NetworkCallProcessor.__init__(self)

      def socket(self, domain, socket_type, protocol):
        print "Creating socket with arguments: %d, %d, %d!" 
        ...
        ...
        # Return an integer as a pseudo socket file descriptor.
        return sock_fd
"""


class NetworkCallProcessor:
  """
  This is the base network call processor. To use this class,
  a new class must inherit NetworkCallProcess and overload all
  the functions defined below.
  """

  def __init__(self):
    pass

  
  def call_socket(*args):
    """
    This function needs to be defined by the class that 
    inherits this object.
    """
    raise ProcessCallNotDefined("call_socket has not been defined!")

  
  def call_connect(*args):
    """
    This function needs to be defined by the class that 
    inherits this object.
    """
    raise ProcessCallNotDefined("call_connect has not been defined!")
      

  def call_listen(*args):
    """
    This function needs to be defined by the class that 
    inherits this object.
    """
    raise ProcessCallNotDefined("call_listen has not been defined!")


  def call_accept(*args):
    """
    This function needs to be defined by the class that 
    inherits this object.
    """
    raise ProcessCallNotDefined("call_accept has not been defined!")


  def call_bind(*args):
    """
    This function needs to be defined by the class that 
    inherits this object.
    """
    raise ProcessCallNotDefined("call_bind has not been defined!")


  def call_send(*args):
    """
    This function needs to be defined by the class that 
    inherits this object.
    """
    raise ProcessCallNotDefined("call_send has not been defined!")


  def call_recv(*args):
    """
    This function needs to be defined by the class that 
    inherits this object.
    """
    raise ProcessCallNotDefined("call_recv has not been defined!")


  def call_sendto(*args):
    """
    This function needs to be defined by the class that 
    inherits this object.
    """
    raise ProcessCallNotDefined("call_sendto has not been defined!")


  def call_recvfrom(*args):
    """
    This function needs to be defined by the class that 
    inherits this object.
    """
    raise ProcessCallNotDefined("call_recvfrom has not been defined!")


  def call_select(*args):
    """
    This function needs to be defined by the class that 
    inherits this object.
    """
    raise ProcessCallNotDefined("call_select has not been defined!")


  def call_getsockopt(*args):
    """
    This function needs to be defined by the class that 
    inherits this object.
    """
    raise ProcessCallNotDefined("call_getsockopt has not been defined!")


  def call_setsockopt(*args):
    """
    This function needs to be defined by the class that 
    inherits this object.
    """
    raise ProcessCallNotDefined("call_setsockopt has not been defined!")

   
  def call_close(*args):
    """
    This function needs to be defined by the class that 
    inherits this object.
    """
    raise ProcessCallNotDefined("call_close has not been defined!")  




# ===========================================================================
# Define Exceptions
# ===========================================================================
class ProcessCallNotDefined(Exception):
  """
  Error raised if a particular network processing call is
  not defined.
  """
  pass
