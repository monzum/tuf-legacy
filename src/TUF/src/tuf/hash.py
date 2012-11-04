"""
<Program Name>
  hash.py

<Author>
  Vladimir Diaz <vladimir.v.diaz@gmail.com>

<Started>
  February 28, 2012.  Based on a previous version of this module.

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Support multiple implementations of secure hash and message digest
  algorithms. Any hash-related routines that TUF requires should be
  located in this module.  Ensuring that a secure hash algorithm is
  available to TUF, simplifying the creation of digest objects, and
  providing a central location for hash routines are the main goals
  of this module.  Support routines implemented include functions to 
  create digest objects given a filename or file object.
  Hashlib and pycrypto hash algorithms currently supported.

"""


# Import tuf Exceptions.
import tuf

# Import tuf logger to log warning messages.
import logging
logger = logging.getLogger('tuf.hash')

# The list of hash libraries imported successfully.
_supported_libraries = []

# Hash libraries currently supported by tuf.hash.
_SUPPORTED_LIB_LIST = ['hashlib', 'pycrypto'] 

# Let's try importing the pycrypto hash algorithms.  Pycrypto will
# not be added to the supported list of libraries if the specified
# hash algorithms below cannot all be imported.
try:
  from Crypto.Hash import MD5
  from Crypto.Hash import SHA
  from Crypto.Hash import SHA224
  from Crypto.Hash import SHA256
  from Crypto.Hash import SHA384
  from Crypto.Hash import SHA512
  _supported_libraries.append('pycrypto')
except ImportError:
  logger.warn('Pycrypto hash algorithms could not be imported.  '
              'Supported libraries: '+str(_SUPPORTED_LIB_LIST))

  pass

# Python <=2.4 does not have the hashlib module by default.
# Let's try importing hashlib and adding it to our supported list.
try:
  import hashlib
  _supported_libraries.append('hashlib')
except ImportError:
  logger.warn('Hashlib could not be imported.  '
              'Supported libraries: '+str(_SUPPORTED_LIB_LIST)) 
  pass

# Were we able to import any hash libraries?
if not _supported_libraries:
  # This is fatal, we'll have no way of generating hashes.
  raise tuf.Error('Unable to import a hash library from the '
                  'following supported list: '+str(_SUPPORTED_LIB_LIST)) 


_DEFAULT_HASH_ALGORITHM = 'sha256'
_DEFAULT_HASH_LIBRARY = 'hashlib'





def digest(algorithm=_DEFAULT_HASH_ALGORITHM, 
           hash_library=_DEFAULT_HASH_LIBRARY):
  """
  <Purpose>
    Provide the caller with the ability to create
    digest objects without having to worry about hash
    library availability or which library to use.  
    The caller also has the option of specifying which
    hash algorithm and/or library to use.

    # Creation of a digest object using defaults
    # or by specifying hash algorithm and library.
    digest_object = tuf.hash.digest()
    digest_object = tuf.hash.digest('sha384')
    digest_object = tuf.hash.digest('pycrypto')

    # The expected interface for digest objects. 
    digest_object.digest_size
    digest_object.hexdigest()
    digest_object.update('data')
    digest_object.digest()
    
    # Added hash routines by this module.
    digest_object = tuf.hash.digest_fileobject(file_object)
    digest_object = tuf.hash.digest_filename(filename)
  
  <Arguments>
    algorithm:
      The hash algorithm (e.g., md5, sha1, sha256).

    hash_library:
      The library providing the hash algorithms 
      (e.g., pycrypto, hashlib).
      
  <Exceptions>
    tuf.UnsupportedAlgorithmError
    tuf.UnsupportedLibraryError

  <Side Effects>
    None.

  <Returns>
    Digest object (e.g., hashlib.new(algorithm) or 
    algorithm.new() # pycrypto).

  """

  # Was a hashlib digest object requested and is it supported?
  # If so, return the digest object.
  if hash_library == 'hashlib' and hash_library in _supported_libraries:
    try:
      return hashlib.new(algorithm)
    except ValueError:
      raise tuf.UnsupportedAlgorithmError(algorithm)

  # Was a pycrypto digest object requested and is it supported?
  elif hash_library == 'pycrypto' and hash_library in _supported_libraries:
    # Pycrypto does not offer a comparable hashlib.new(hashname).
    # Let's first check the 'algorithm' argument before returning
    # the correct pycrypto digest object using pycrypto's object construction. 
    if algorithm == 'md5':
      return MD5.new()
    elif algorithm == 'sha1':
      return SHA.new()
    elif algorithm == 'sha224':
      return SHA224.new()
    elif algorithm == 'sha256':
      return SHA256.new()
    elif algorithm == 'sha384':
      return SHA384.new()
    elif algorithm == 'sha512':
      return SHA512.new()
    else:
      raise tuf.UnsupportedAlgorithmError(algorithm)
  
  # The requested hash library is not supported. 
  else:
    raise tuf.UnsupportedLibraryError('Unsupported library requested.  '
                    'Supported hash libraries: '+str(_SUPPORTED_LIB_LIST)) 





def digest_fileobject(file_object, algorithm=_DEFAULT_HASH_ALGORITHM,
                      hash_library=_DEFAULT_HASH_LIBRARY):
  """
  <Purpose>
    Generate a digest object given a file object.  The new digest object
    is updated with the contents of 'file_object' prior to returning the
    object to the caller.
      
  <Arguments>
    file_object:
      File object whose contents will be used as the data
      to update the hash of a digest object to be returned.

    algorithm:
      The hash algorithm (e.g., md5, sha1, sha256).

    hash_library:
      The library providing the hash algorithms 
      (e.g., pycrypto, hashlib).

  <Exceptions>
    tuf.UnsupportedAlgorithmError
    tuf.Error

  <Side Effects>
    Calls tuf.hash.digest() to create the actual digest object.

  <Returns>
    Digest object (e.g., hashlib.new(algorithm) or 
    algorithm.new() # pycrypto).

  """

  # Digest object returned whose hash will be updated using 'file_object'.
  # digest() raises:
  # tuf.UnsupportedAlgorithmError
  # tuf.Error
  digest_object = digest(algorithm, hash_library)

  # Defensively seek to beginning, as there's no case where we don't
  # intend to start from the beginning of the file.
  file_object.seek(0)

  # Read the contents of the file object in at most 4096-byte chunks.
  # Update the hash with the data read from each chunk and return after
  # the entire file is processed. 
  while True:
    chunksize = 4096
    data = file_object.read(chunksize)
    if not data:
      break
    digest_object.update(data_to_string(data))
  return digest_object





def digest_filename(filename, algorithm=_DEFAULT_HASH_ALGORITHM,
                    hash_library=_DEFAULT_HASH_LIBRARY):
  """
  <Purpose>
    Generate a digest object, update its hash using a file object
    specified by filename, and then return it to the caller.

  <Arguments>
    filename:
      The filename belonging to the file object to be used. 
    
    algorithm:
      The hash algorithm (e.g., md5, sha1, sha256).

    hash_library:
      The library providing the hash algorithms 
      (e.g., pycrypto, hashlib).

  <Exceptions>
    tuf.UnsupportedAlgorithmError
    tuf.Error 

  <Side Effects>
    Calls tuf.hash.digest_fileobject() after opening 'filename'.
    File closed before returning.

  <Returns>
    Digest object (e.g., hashlib.new(algorithm) or 
    algorithm.new() # pycrypto).

  """

  # Open 'filename' in read+binary mode.
  file_object = open(filename, 'rb')
  
  # Create digest_object and update its hash data from file_object.
  # digest_fileobject() raises:
  # tuf.UnsupportedAlgorithmError
  # tuf.Error
  digest_object = digest_fileobject(file_object, algorithm, hash_library)
  
  file_object.close()
  return digest_object





def data_to_string(data):
  """
  <Purpose>
    Return 'data' as a string.  The update() function of a digest object
    only accepts strings, however, TUF will often need to feed this function
    non-strings.  This utility function circumvents this issue and decides how
    exactly to convert these objects TUF might use.

  <Arguments>
    data:
      The data object to be returned as a string. 

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    String.

  """

  if isinstance(data, str):
    return data
  elif isinstance(data, unicode):
    return data.encode("utf-8")
  else:
    return str(data)
