"""
<Program Name>
  signercli.py

<Author>
  Vladimir Diaz <vladimir.v.diaz@gmail.com>

<Started>
  April 5, 2012.  Based on a previous version of this module by Geremy Condra.

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provide an interactive command-line interface to create and sign metadata.
  This script can be used to create all of the top-level role files required
  by TUF, which include 'root.txt', 'targets.txt', 'release.txt', and
  'timestamp.txt'. It also provides options to generate RSA keys, change the
  encryption/decryption keys of encrypted key files, list the keyids of
  the signing keys stored in a keystore directory, create delegated roles,
  and dump the contents of signing keys (i.e., public and private keys, key
  type, etc.)

  This module can be best understood if read starting with the parse_option()
  call in __main__.  All of the options accept a single keystore
  directory argument.  Beyond this point, the script is interactive.
  If any additional arguments is required, the user will be asked to input
  these values.  The script will process one command-line option and
  raise an error for any other other options that might be supplied.

  Initially, the 'quickstart.py' script is utilized when the repository is
  first created.  'signercli.py' would then be executed to update the state
  of the repository.  For example, the repository owner wants to change the
  'targets.txt' signing key.  The owner would run 'signercli.py' to
  generate a new RSA key, add the new key to the configuration file created
  by 'quickstart.py', and then run 'signercli' to update the metadata files.

<Usage>
  $ python signercli.py --<option> <keystore_directory>

  Examples:
  S python signercli.py --genrsakey ./keystore
  $ python signercli.py --changepass ./keystore

<Options>
  See the parse_options() function for the full list of supported options.

"""

import os
import optparse
import getpass
import sys
import logging

import tuf
import tuf.repo.signerlib
import tuf.repo.keystore
import tuf.util
import tuf.log

json = tuf.util.import_json()

# See 'log.py' to learn how logging is handled in TUF.
logger = logging.getLogger('tuf.signercli')

# The maximum number of attempts the user has to enter
# valid input.
MAX_INPUT_ATTEMPTS = 3


def _check_directory(directory):
  try:
    directory = tuf.repo.signerlib.check_directory(directory)
  except (tuf.FormatError, tuf.Error), e:
    message = str(e)+'\n'
    raise tuf.RepositoryError(message)

  return directory




def _get_password(prompt='Password: ', confirm=False):
  """
    Return the password entered by the user.  If 'confirm'
    is True, the user is asked to enter the previously
    entered password once again.  If they match, the
    password is returned to the caller.

  """

  while True:
    password = getpass.getpass(prompt, sys.stderr)
    if not confirm:
      return password
    password2 = getpass.getpass('Confirm: ', sys.stderr)
    if password == password2:
      return password
    else:
      print 'Mismatch; try again.'





def _prompt(message, result_type=str):
  """
    Prompt the user for input by printing 'message', converting
    the input to 'result_type', and returning the value to the
    caller.

  """

  return result_type(raw_input(message))





def _get_metadata_directory():
  """
    Get the metadata directory from the user.  The user
    is asked to enter the directory, and if validated, is
    returned to the caller.  'tuf.FormatError' is raised
    if the directory is not properly formatted, and 'tuf.Error'
    if it does not exist.

  """

  metadata_directory = _prompt('\nEnter the metadata directory: ', str)

  # Raises 'tuf.FormatError' or 'tuf.Error'.
  metadata_directory = _check_directory(metadata_directory)

  return metadata_directory





def _list_keyids(keystore_directory):
  """
    List the key files found in 'keystore_directory'.
    It is assumed the directory exists and has been validated by
    the caller.  The keyids are listed without the '.key' extension.

  """

  # Extract the key files ending in a '.key' extension.
  key_paths = []
  for filename in os.listdir(keystore_directory):
    full_path = os.path.join(keystore_directory, filename)
    if filename.endswith('.key') and not os.path.isdir(full_path):
      key_paths.append(filename)

  # Print the keys without the '.key' extension.
  print '\nListing the keyids in '+repr(keystore_directory)
  for keyid in key_paths:
    print keyid[0:keyid.rfind('.key')]





def _get_keyids(keystore_directory):
  """
    Load the keyids in 'keystore_directory'.  The keystore
    database is populated with the keyids that are found
    and successfully loaded.  A list containing the keyids
    of the loaded keys is returned to the caller.  Since the
    key files are stored in encrypted form, the user is asked
    to enter the password that was used to encrypt the key
    file.

  """

  # The keyids list containing the keys loaded.
  loaded_keyids = []

  # Save the 'load_keystore_from_keyfiles' function call.
  load_key = tuf.repo.keystore.load_keystore_from_keyfiles

  # Ask the user for the keyid and password.  Next, try to load specified
  # keyid/password combination.  If loaded, append the loaded key's keyid
  # to 'loaded_keyids'.  Loop the steps above or exit when the user enters
  # 'quit'.
  while True:
    keyid_prompt = '\nEnter the keyid or "quit" when done: '
    keyid = _prompt(keyid_prompt, str)
    if keyid.lower() == 'quit':
      break

    # Get the password from the user so we can decrypt the key file.
    password = _get_password('\nEnter the keyid\'s password: ')

    # Try to load the keyfile with the keyid and password credentials.
    loaded_keyid = load_key(keystore_directory, [keyid], [password])
    # Was 'keyid' loaded?
    if keyid not in loaded_keyid:
      logger.error('Could not load keyid: '+keyid)
      continue

    # Append 'keyid' to the loaded list of keyids.
    loaded_keyids.append(loaded_keyid[0])

  return loaded_keyids





def _get_all_config_keyids(config_filepath, keystore_directory):
  """
    Retrieve the contents of the config file and load
    the keys for the top-level roles.  After this function
    returns successfully, all the required roles are loaded
    in the keystore.  The arguments should be absolute paths.

    <Exceptions>
      tuf.Error, if the required top-level keys could
      not be loaded.

    <Returns>
      A dictionary containing the keyids for the top-level roles.
      loaded_keyids = {'root': [1233d3d, 598djdks, ..],
                       'release': [sdfsd323, sdsd9090s, ..]
                       ...}

  """

  # Save the 'load_keystore_from_keyfiles' function call.
  load_key = tuf.repo.keystore.load_keystore_from_keyfiles

  # 'tuf.Error' raised if the configuration file cannot be read.
  config_dict = tuf.repo.signerlib.read_config_file(config_filepath)

  loaded_keyids = {}
  # Extract the sections from the config file.  We are only
  # interested in role sections.
  for key, value in config_dict.items():
    if key in ['root', 'targets', 'release', 'timestamp']:
      # Try to load the keyids for each role.
      loaded_keyids[key] = []
      for keyid in value['keyids']:
        for attempt in range(MAX_INPUT_ATTEMPTS):
          message = '\nEnter the password for the '+key+' role ('+keyid+'): '
          password = _get_password(message)
          loaded_key = load_key(keystore_directory, [keyid], [password])
          if not loaded_key or keyid not in loaded_key:
            logger.error('Could not load keyid: '+keyid)
            continue
          loaded_keyids[key].append(keyid)
          break
        if keyid not in loaded_keyids[key]:
          raise tuf.Error('Could not load a required top-level role key')

  # Ensure we loaded keys for the required top-level roles.
  for key in ['root', 'targets', 'release', 'timestamp']:
    if key not in loaded_keyids:
      message = 'The configuration file did not contain the required roles'
      raise tuf.Error(message)

  return loaded_keyids





def _get_role_config_keyids(config_filepath, keystore_directory, role):
  """
    Retrieve and load the key(s) for 'role', as listed in the keyids
    found in 'config_filepath'.  'config_filepath' and 'keystore_directory'
    should be absolute paths.

  <Exceptions>
    tuf.Error, if the required keys could not be loaded.

  """

  # Save the 'load_keystore_from_keyfiles' function call.
  load_key = tuf.repo.keystore.load_keystore_from_keyfiles

  # 'tuf.Error' raised if the configuration file cannot be read.
  config_dict = tuf.repo.signerlib.read_config_file(config_filepath)

  role_keyids = []
  # Extract the sections from the config file.  We are only interested
  # in the 'role' section.
  for key, value in config_dict.items():
    if key == role:
      for keyid in value['keyids']:
        for attempt in range(MAX_INPUT_ATTEMPTS):
          message = '\nEnter the password for the '+key+' role ('+keyid+'): '
          password = _get_password(message)
          loaded_key = load_key(keystore_directory, [keyid], [password])
          if not loaded_key or keyid not in loaded_key:
            print 'Could not load keyid: '+keyid
            logger.error('Could not load keyid: '+keyid)
            continue
          role_keyids.append(keyid)
          break
      # Ensure we loaded all the keyids.
      for keyid in value['keyids']:
        if keyid not in role_keyids:
          raise tuf.Error('Could not load a required role key')
  if not role_keyids:
    raise tuf.Error('Could not load the required keys for '+role)

  return role_keyids





def _sign_and_write_metadata(metadata, keyids, filename):
  """
    Sign 'metadata' and write it to 'filename' (an absolute path),
    overwriting the original file if it exists.  If any of the
    keyids have already signed the file, the old signatures of
    those keyids will be replaced.

  <Exceptions>
    tuf.FormatError, if any of the arguments are incorrectly formatted.

    tuf.Error, if an error is encountered.

  """

  # Sign the metadata object.  The 'signable' object contains the keyids
  # used in the signing process, including the signatures generated.
  signable = tuf.repo.signerlib.sign_metadata(metadata, keyids, filename)

  # Write the 'signable' object to 'filename'.  The 'filename' file is
  # the final metadata file, such as 'root.txt' and 'targets.txt'.
  tuf.repo.signerlib.write_metadata_file(signable, filename)





def change_password(keystore_directory):
  """
  <Purpose>
    Change the password for the signing key specified by the user.
    All the values required by the user will be interactively
    retrieved by this function.

  <Arguments>
    keystore_directory:
      The directory containing the signing keys (i.e., key files ending
      in '.key').

  <Exceptions>
    tuf.RepositoryError, if an an error occurred while updating the repository.

  <Side Effects>
    The key file specified by the user is modified, including the encryption
    key.

  <Returns>
    None.

  """

  # Save the 'load_keystore_from_keyfiles' function call.
  load_key = tuf.repo.keystore.load_keystore_from_keyfiles

  # Verify the 'keystore_directory' argument.
  keystore_directory = _check_directory(keystore_directory)

  # List the keyids in the keystore and prompt the user for the keyid they
  # wish to modify.
  _list_keyids(keystore_directory)

  # Retrieve the keyid from the user.
  message = '\nEnter the keyid for the password you wish to change: '
  keyid = _prompt(message, str)

  # Get the old password from the user.
  old_password_prompt = '\nEnter the old password for the keyid: '
  old_password = _get_password(old_password_prompt)

  # Try to load the keyfile
  loaded_keys = load_key(keystore_directory, [keyid], [old_password])

  # Was 'keyid' loaded?
  if keyid not in loaded_keys:
    message = 'Could not load keyid: '+keyid+'\n'
    raise tuf.RepositoryError(message)

  # Retrieve the new password.
  new_password = _get_password('\nNew password: ', confirm=True)

  # Now that we have all the required information, try to change the password.
  try:
    tuf.repo.keystore.change_password(keyid, old_password, new_password)
  except (tuf.BadPasswordError, tuf.UnknownKeyError), e:
    message = str(e)+'\n'
    raise tuf.RepositoryError(message)

  # Save the changes.
  tuf.repo.keystore.save_keystore_to_keyfiles(keystore_directory)





def generate_rsa_key(keystore_directory):
  """
  <Purpose>
    Generate an RSA key and save it to the keystore directory.

  <Arguments>
    keystore_directory:
      The directory containing the signing keys (i.e., key files ending
      in '.key').

  <Exceptions>
    tuf.RepositoryError, if an an error occurred while updating the repository.

  <Side Effects>
    An RSA key will be generated and added to tuf.repo.keystore.
    The RSA key will be saved to the keystore directory specified
    on the command-line.

  <Returns>
    None.

  """

  # Save a reference to the generate_and_save_rsa_key() function.
  save_rsa_key = tuf.repo.signerlib.generate_and_save_rsa_key

  # Verify the 'keystore_directory' argument.
  keystore_directory = _check_directory(keystore_directory)

  # Retrieve the number of bits for the RSA key from the user.
  rsa_key_bits = _prompt('\nEnter the number of bits for the RSA key: ', int)

  # Retrieve the password used to encrypt/decrypt the key file from the user.
  message = '\nEnter a password to encrypt the generated RSA key: '
  password = _get_password(message, confirm=True)

  # Generate the RSA key and save it to 'keystore_directory'.
  try:
    save_rsa_key(keystore_directory=keystore_directory,
                 password=password, bits=rsa_key_bits)
  except (tuf.FormatError, tuf.CryptoError), e:
    message = 'The RSA key could not be generated. '+str(e)+'\n'
    raise tuf.RepositoryError(message)





def list_signing_keys(keystore_directory):
  """
  <Purpose>
    Print the key IDs of the signing keys listed in the keystore
    directory.

  <Arguments>
    keystore_directory:
      The directory containing the signing keys (i.e., key files ending
      in '.key').

  <Exceptions>
    tuf.RepositoryError, if an an error occurred while updating the repository.

  <Side Effects>
    None.

  <Returns>
    None.

  """

  # Verify the 'keystore_directory' argument.
  keystore_directory = _check_directory(keystore_directory)

  _list_keyids(keystore_directory)





def dump_key(keystore_directory):
  """
  <Purpose>
    Dump the contents of the signing key specified by the user.
    This dumped information includes the keytype, signing method,
    the public key, and the private key (if requested by the user).

  <Arguments>
    keystore_directory:
      The directory containing the signing keys (i.e., key files ending
      in '.key').

  <Exceptions>
    tuf.RepositoryError, if an an error occurred while updating the repository.

  <Side Effects>
    The contents of encrypted key files are extracted and printed.

  <Returns>
    None.

  """

  # Save the 'load_keystore_from_keyfiles' function call.
  load_key = tuf.repo.keystore.load_keystore_from_keyfiles

  # Verify the 'keystore_directory' argument.
  keystore_directory = _check_directory(keystore_directory)

  # List the keyids found in 'keystore_directory', minus the '.key' extension.
  _list_keyids(keystore_directory)

  # Retrieve the keyid and password from the user.
  message = '\nEnter the keyid for the signing key you wish to dump: '
  keyid = _prompt(message, str)
  password = _get_password('\nEnter the password for the keyid: ')

  print
  print keyid
  print password

  # Try to load the keyfile
  loaded_keys = load_key(keystore_directory, [keyid], [password])

  # Was 'keyid' loaded?
  if keyid not in loaded_keys:
    message = 'Could not load keyid: '+keyid+'\n'
    raise tuf.RepositoryError(message)

  # Get the key object.
  key = tuf.repo.keystore.get_key(keyid)

  # Ask the user if they would like to print the private key as well.
  show_private = False
  prompt = 'Should the private key be printed as well?' \
           ' (if yes, enter \'private\'): '
  print '\n*WARNING* Printing the private key reveals' \
        ' sensitive information *WARNING*'
  input = _prompt(prompt, str)
  if input.lower() == 'private':
    show_private = True

  # Retrieve the key metadata according to the keytype.
  if key['keytype'] == 'rsa':
    key_metadata = tuf.rsa_key.create_in_metadata_format(key['keyval'],
                                                         private=show_private)
  else:
    message = 'The keystore contains an invalid key type.'
    raise tuf.RepositoryError(message)

  # Print the contents of the key metadata.
  print json.dumps(key_metadata, indent=2, sort_keys=True)





def make_root_metadata(keystore_directory):
  """
  <Purpose>
    Create the 'root.txt' file.

  <Arguments>
    keystore_directory:
      The directory containing the signing keys (i.e., key files ending
      in '.key').

  <Exceptions>
    tuf.RepositoryError, if an an error occurred while updating the repository.

  <Side Effects>
    The contents of an existing root metadata file is overwritten.

  <Returns>
    None.

  """

  # Verify the 'keystore_directory' argument.
  keystore_directory = _check_directory(keystore_directory)

  # Get the metadata directory and the metadata filenames.
  try:
    metadata_directory = _get_metadata_directory()
  except (tuf.FormatError, tuf.Error), e:
    message = str(e)+'\n'
    raise tuf.RepositoryError(message)
  filenames = tuf.repo.signerlib.get_metadata_filenames(metadata_directory)

  # Get the configuration file.
  config_filepath = _prompt('\nEnter the configuration file path: ', str)
  config_filepath = os.path.abspath(config_filepath)

  # Load the keys for the top-level roles.
  try:
    loaded_keyids = _get_all_config_keyids(config_filepath, keystore_directory)
  except (tuf.Error, tuf.FormatError), e:
    message = str(e)+'\n'
    raise tuf.RepositoryError(message)
  root_keyids = loaded_keyids['root']

  # Generate the root metadata and write it to 'root.txt'.
  try:
    tuf.repo.signerlib.build_root_file(config_filepath, root_keyids,
                                       metadata_directory)
  except (tuf.FormatError, tuf.Error), e:
    message = str(e)+'\n'
    raise tuf.RepositoryError(message)




def make_targets_metadata(keystore_directory):
  """ 
  <Purpose>
    Create the 'targets.txt' metadata file.  The targets must exist at the
    same path they should on the repository.  This takes a list of targets.
    We're not worrying about custom metadata at the moment. It's allowed to
    not provide keys.

  <Arguments>
    keystore_directory:
      The directory containing the signing keys (i.e., key files ending
      in '.key').

  <Exceptions>
    tuf.RepositoryError, if an an error occurred while updating the repository.

  <Side Effects>
    The contents of an existing targets metadata file is overwritten.

  <Returns>
    None.

  """

  # Verify the 'keystore_directory' argument.
  keystore_directory = _check_directory(keystore_directory)

  # Retrieve the target files.
  prompt_targets = '\nEnter the directory containing the target files: '
  target_directory = _prompt(prompt_targets, str)

  # Verify 'target_directory'.
  target_directory = _check_directory(target_directory)

  # Retrieve the metadata directory and the 'targets' filename.
  try:
    metadata_directory = _get_metadata_directory()
  except (tuf.FormatError, tuf.Error), e:
    message = str(e)+'\n'
    raise tuf.RepositoryError(message)

  # Get the configuration file.
  config_filepath = _prompt('\nEnter the configuration file path: ', str)

  config_filepath = os.path.abspath(config_filepath)

  try:
    # Retrieve and load the 'targets' signing keys.
    targets_keyids = _get_role_config_keyids(config_filepath,
                                           keystore_directory, 'targets')
  except (tuf.FormatError, tuf.Error), e:
    message = str(e)+'\n'
    raise tuf.RepositoryError(message)

  try:
    # Create, sign, and write the "targets.txt" file.
    tuf.repo.signerlib.build_targets_file(target_directory, targets_keyids,
                                       metadata_directory)
  except (tuf.FormatError, tuf.Error), e:
    message = str(e)+'\n'
    raise tuf.RepositoryError(message)






def make_release_metadata(keystore_directory):
  """
  <Purpose>
    Create the release metadata file.
    The minimum metadata must exist. This is root.txt and targets.txt.

  <Arguments>
    keystore_directory:
      The directory containing the signing keys (i.e., key files ending
      in '.key').

  <Exceptions>
    tuf.RepositoryError, if an an error occurred while updating the repository.

  <Side Effects>
    The contents of an existing release metadata file is overwritten.

  <Returns>
    None.

  """

  # Verify the 'keystore_directory' argument.
  keystore_directory = _check_directory(keystore_directory)

  # Retrieve the metadata directory and the release filename.
  try:
    metadata_directory = _get_metadata_directory()
  except (tuf.FormatError, tuf.Error), e:
    message = str(e)+'\n'
    raise tuf.RepositoryError(message)
  filenames = tuf.repo.signerlib.get_metadata_filenames(metadata_directory)
  release_filename = filenames['release']

  # Get the configuration file.
  config_filepath = _prompt('\nEnter the configuration file path: ', str)
  config_filepath = os.path.abspath(config_filepath)

  # Retrieve and load the 'release' signing keys.
  try:
    release_keyids = _get_role_config_keyids(config_filepath,
                                              keystore_directory, 'release')
    # Generate the root metadata and write it to 'release.txt'
    tuf.repo.signerlib.build_release_file(release_keyids, metadata_directory)
  except (tuf.FormatError, tuf.Error), e:
    message = str(e)+'\n'
    raise tuf.RepositoryError(message)





def make_timestamp_metadata(keystore_directory):
  """
  <Purpose>
    Create the timestamp metadata file.  The 'release.txt' file must exist.

  <Arguments>
    keystore_directory:
      The directory containing the signing keys (i.e., key files ending
      in '.key').

  <Exceptions>
    tuf.RepositoryError, if an an error occurred while updating the repository.

  <Side Effects>
    The contents of an existing timestamp metadata file is overwritten.

  <Returns>
    None.

  """

  # Verify the 'keystore_directory' argument.
  keystore_directory = _check_directory(keystore_directory)


  # Retrieve the metadata directory and the timestamp filename.
  try:
    metadata_directory = _get_metadata_directory()
  except (tuf.FormatError, tuf.Error), e:
    message = str(e)+'\n'
    raise tuf.RepositoryError(message)
  filenames = tuf.repo.signerlib.get_metadata_filenames(metadata_directory)
  timestamp_filename = filenames['timestamp']

  # Get the configuration file.
  config_filepath = _prompt('\nEnter the configuration file path: ', str)
  config_filepath = os.path.abspath(config_filepath)

  # Retrieve and load the 'timestamp' signing keys.
  try:
    timestamp_keyids = _get_role_config_keyids(config_filepath,
                                               keystore_directory, 'timestamp')
    # Generate the root metadata and write it to 'timestamp.txt'
    tuf.repo.signerlib.build_timestamp_file(timestamp_keyids,
                                            metadata_directory)
  except (tuf.FormatError, tuf.Error), e:
    message = str(e)+'\n'
    raise tuf.RepositoryError(message)





def sign_metadata_file(keystore_directory):
  """
  <Purpose>
    Sign the metadata file specified by the user.

  <Arguments>
    keystore_directory:
      The directory containing the signing keys (i.e., key files ending
      in '.key').

  <Exceptions>
    tuf.RepositoryError, if an an error occurred while updating the repository.

  <Side Effects>
    The contents of an existing metadata file is overwritten.

  <Returns>
    None.

  """

  # Verify the 'keystore_directory' argument.
  keystore_directory = _check_directory(keystore_directory)

  # List the keyids available in the keystore.
  _list_keyids(keystore_directory)

  # Retrieve the keyids of the signing keys from the user.
  print '\nThe keyids that will sign the metadata file must be loaded.'
  loaded_keyids = _get_keyids(keystore_directory)

  if len(loaded_keyids) == 0:
    message = 'No keyids were loaded\n'
    raise tuf.RepositoryError(message)

  # Retrieve the metadata file the user intends to sign.
  metadata_filename = _prompt('\nEnter the metadata filename: ', str)

  metadata_filename = os.path.abspath(metadata_filename)
  if not os.path.isfile(metadata_filename):
    message = repr(metadata_filename)+' is an invalid file.\n'
    raise tuf.RepositoryError(message)

  # Create, sign, and write the metadata file.
  metadata = tuf.repo.signerlib.read_metadata_file(metadata_filename)
  _sign_and_write_metadata(metadata, loaded_keyids, metadata_filename)





def make_delegation(keystore_directory):
  """
  <Purpose>
    Create a delegation by updating the 'delegations' field of 'targets.txt'
    and creating the delegated role's metadata file.  The user specifies the
    delegated role's name and target files.  The 'targets.txt' file must exist.

  <Arguments>
    keystore_directory:
      The directory containing the signing keys (i.e., key files ending
      in '.key').

  <Exceptions>
    tuf.RepositoryError, if an an error occurred while updating the repository.

  <Side Effects>
    The targets metadata file is modified.  The 'delegations' field of
    'targets.txt' is added.

  <Returns>
    None.

  """

  # Verify the 'keystore_directory' argument.
  keystore_directory = _check_directory(keystore_directory)

  # Get the metadata directory.
  try:
    metadata_directory = _get_metadata_directory()
  except (tuf.FormatError, tuf.Error), e:
    message = str(e)+'\n'
    raise tuf.RepositoryError(message)

  # Get the delegated role's target directory, which should be located within
  # the repository's targets directory.  We need this directory to generate the
  # delegated role's target paths.
  prompt = '\nNOTE: The directory entered below should be located within the '+\
    'repository\'s targets directory.\nEnter the directory containing the '+\
    'delegated role\'s target files: '
  delegated_targets_directory = _prompt(prompt, str)

  # Verify 'delegated_targets_directory'.
  try:
    tuf.repo.signerlib.check_directory(delegated_targets_directory)
  except (tuf.FormatError, tuf.Error), e:
    message = str(e)+'\n'
    raise tuf.RepositoryError(message)

  # Get all the target roles and their respective keyids.
  # These keyids will let the user know which roles are currently known.
  # signerlib.get_target_keyids() returns a dictionary that looks something
  # like this: {'targets':[keyid1, ...], 'targets/role1':[keyid], ...}
  targets_roles = tuf.repo.signerlib.get_target_keyids(metadata_directory)

  # Get the parent role.  We need to modify the parent role's metadata file.
  print '\nListing "targets" and all available delegated roles.'
  for section in targets_roles.keys():
    print section
  parent_role = None
  # Retrieve the parent role from the user.
  for attempt in range(MAX_INPUT_ATTEMPTS):
    prompt = '\nChoose and enter the parent role\'s full name: '
    parent_role = _prompt(prompt, str)
    if parent_role not in targets_roles:
      print '\nInvalid role name entered'
      parent_role = None
      continue
    else:
      break

  # Ensure we loaded a valid parent role.
  if parent_role is None:
    message = 'Could not get a valid parent role.\n'
    raise tuf.RepositoryError(message)

  # 'load_key' is a reference to the 'load_keystore_from_keyfiles function'.
  load_key = tuf.repo.keystore.load_keystore_from_keyfiles

  # Load the parent's key(s).  The key needs to be loaded because
  # its metadata file will be modified.
  parent_keyids = []
  for keyid in targets_roles[parent_role]:
    for attempt in range(MAX_INPUT_ATTEMPTS):
      prompt = 'Enter the password for '+parent_role+' ('+keyid+'): '
      password = _get_password(prompt)
      loaded_keyid = load_key(keystore_directory, [keyid], [password])
      if keyid not in loaded_keyid:
        print '\nThe keyid could not be loaded.'
        continue
      parent_keyids.append(loaded_keyid[0])
      break
    if keyid not in parent_keyids:
      message = 'Could not load the keys for the parent role.\n'
      raise tuf.RepositoryError(message)

  # Retrieve the delegated rolename from the user (e.g., 'role1').
  delegated_role = _prompt('\nEnter the delegated role\'s name: ', str)

  # List the keyids available in the keystore.  The user will next
  # identify the keyid for the new delegated role.
  _list_keyids(keystore_directory)

  # Retrieve the delegated role\'s keyid from the user.
  print '\nThe keyid of the delegated role must be loaded.'
  delegated_keyid = _get_keyids(keystore_directory)

  # Ensure we actually loaded one delegated key.  Delegated roles
  # should have only one signing key.
  if len(delegated_keyid) != 1:
    message = 'Only one key must be loaded for the delegated role\n'
    raise tuf.RepositoryError(message)
  delegated_keyid = delegated_keyid[0]

  # Retrieve the file paths for the delegated targets.
  delegated_paths = []
  for filename in os.listdir(delegated_targets_directory):
    full_path = os.path.join(delegated_targets_directory, filename)
    if os.path.isfile(full_path):
      # The target paths need to be relative to the repository's targets
      # directory (e.g., 'targets/role1/target_file.txt').
      # [len(repository_directory)+1:] strips the repository path, including
      # its trailing path separator.
      repository_directory, junk = os.path.split(metadata_directory)
      delegated_path = delegated_targets_directory[len(repository_directory)+1:]
      target_path = os.path.join(delegated_path, filename)
      delegated_paths.append(target_path)
  message = 'The target paths for '+repr(delegated_role)+': '+repr(delegated_paths)
  logger.info(message)

  # Create, sign, and write the delegated role's metadata file.
  parent_directory = os.path.join(metadata_directory, parent_role)
  try:
    os.mkdir(parent_directory)
  except OSError, e:
    pass
  delegated_role_filename = delegated_role+'.txt'
  metadata_filename = os.path.join(parent_directory, delegated_role_filename)
  repository_directory, junk = os.path.split(metadata_directory)
  delegated_metadata = tuf.repo.signerlib.generate_targets_metadata(repository_directory,
                                                                    delegated_paths)
  _sign_and_write_metadata(delegated_metadata, [delegated_keyid], metadata_filename)

  # Retrieve the key from the keystore.
  role_key = tuf.repo.keystore.get_key(delegated_keyid)

  # Extract the metadata from the parent role's file.
  parent_filename = os.path.join(metadata_directory, parent_role)
  parent_filename = parent_filename+'.txt'
  parent_signable = tuf.repo.signerlib.read_metadata_file(parent_filename)
  parent_metadata = parent_signable['signed']

  # Extract the delegations structure if it exists.
  delegations = parent_metadata.get('delegations', {})

  # Update the keys field.
  keys = delegations.get('keys', {})
  if role_key['keytype'] == 'rsa':
    keys[delegated_keyid] = tuf.rsa_key.create_in_metadata_format(role_key['keyval'])
  else:
    message = 'Invalid keytype encountered: '+delegated_keyid+'\n'
    raise tuf.RepositoryError(message)
  delegations['keys'] = keys

  # Update the 'roles' field.
  roles = delegations.get('roles', {})
  threshold = 1
  delegated_role = parent_role+'/'+delegated_role
  relative_paths = []
  for path in delegated_paths:
    relative_paths.append(os.path.sep.join(path.split(os.path.sep)[1:]))
  roles[delegated_role] = tuf.formats.make_role_metadata([delegated_keyid],
                                                         threshold,
                                                         relative_paths)
  delegations['roles'] = roles

  # Update the larger metadata structure.
  parent_metadata['delegations'] = delegations

  # Try to write the modified 'targets.txt' file.
  parent_signable = tuf.formats.make_signable(parent_metadata)
  _sign_and_write_metadata(parent_signable, parent_keyids, parent_filename)





def process_option(options):
  """
  <Purpose>
    Determine the command-line option chosen by the user and call its
    corresponding function.  If 'signercli' is invoked with the --genrsakey
    command-line option, its corresponding 'generate_rsa_key()' function
    is called.

  <Arguments>
    options:
      An optparse OptionValues instance, returned by parser.parse_args().

  <Exceptions>
    tuf.RepositoryError, raised by one of the supported option
    functions.

    tuf.Error, if a valid option was not encountered.

  <Side Effects>
    Files in the repository are either created or modified
    depending on the command-line option chosen by the user.

  <Returns>
    None.

  """

  # Determine which option was chosen and call its corresponding
  # internal function with the option's keystore directory argument.
  if options.genrsakey is not None:
    generate_rsa_key(options.genrsakey)
  elif options.listkeys is not None:
    list_signing_keys(options.listkeys)
  elif options.changepass is not None:
    change_password(options.changepass)
  elif options.dumpkey is not None:
    dump_key(options.dumpkey)
  elif options.makeroot is not None:
    make_root_metadata(options.makeroot)
  elif options.maketargets is not None:
    make_targets_metadata(options.maketargets)
  elif options.makerelease is not None:
    make_release_metadata(options.makerelease)
  elif options.maketimestamp is not None:
    make_timestamp_metadata(options.maketimestamp)
  elif options.sign is not None:
    sign_metadata_file(options.sign)
  elif options.makedelegation is not None:
    make_delegation(options.makedelegation)
  else:
    raise tuf.Error('A valid option was not encountered.\n')




def parse_options():
  """
  <Purpose>
    Parse the command-line options.  'signercli' expects a single
    command-line option and one keystore directory argument.
    Example:
      signercli --genrsakey ./keystore

    All supported command-line options expect a single keystore
    directory argument.  If 'signercli' is invoked with an incorrect
    number of command-line options or arguments, a parser error
    is printed and the script exits.

  <Arguments>
    None.

  <Exceptions>
    None.

  <Side Effects>
    A file is a created or modified depending on the option
    encountered on the command-line.

  <Returns>
    The options object returned by the parser's parse_args() method.

  """

  usage = 'usage: %prog [option] <keystore_directory>'
  option_parser = optparse.OptionParser(usage=usage)

  # Add the options supported by 'signercli' to the option parser.
  option_parser.add_option('--genrsakey', action='store', type='string',
                           help='Generate an RSA key and save it to '
                           'the keystore.')

  option_parser.add_option('--listkeys', action='store', type='string',
                           help='List the key IDs of the signing '
                           'keys located in the keystore.')

  option_parser.add_option('--changepass', action='store', type='string',
                           help='Change the password for one of '
                           'the signing keys.')

  option_parser.add_option('--dumpkey', action='store', type='string',
                           help='Dump the contents of an encrypted '
                           'key file.')

  option_parser.add_option('--makeroot', action='store', type='string',
                           help='Create the Root metadata file '
                           '(root.txt).')

  option_parser.add_option('--maketargets', action='store', type='string',
                           help='Create the Targets metadata file '
                           '(targets.txt).')

  option_parser.add_option('--makerelease', action='store', type='string',
                           help='Create the Release metadata file '
                           '(release.txt).')

  option_parser.add_option('--maketimestamp', action='store', type='string',
                           help='Create the Timestamp metadata file '
                           '(timestamp.txt).')

  option_parser.add_option('--sign', action='store', type='string',
                           help='Sign a metadata file.')

  option_parser.add_option('--makedelegation', action='store', type='string',
                           help='Create a delegated role by creating '
                           'its metadata file and updating the parent '
                           'role\'s metadata file.')

  (options, remaining_arguments) = option_parser.parse_args()

  # Ensure the script was invoked with the correct number of arguments
  # (i.e., one command-line option and a single keystore directory argument.
  # Return the options object to the caller to determine the option chosen
  # by the user.  option_parser.error() will print the argument error message
  # and exit.
  if len(sys.argv) != 3:
    option_parser.error('Expected a single option and one keystore argument.')

  return options





if __name__ == '__main__':
  options = parse_options()

  # Process the command-line option chosen by the user.
  # 'tuf.RepositoryError' raised by the option's corresponding
  # function if an error occurred.  'tuf.Error' raised if a valid
  # option was not provided by the user.
  try:
    process_option(options)
  except (tuf.RepositoryError, tuf.Error), e:
    sys.stderr.write('Error: '+str(e))
    sys.exit(1)

  # The command-line option was processed successfully.
  sys.exit(0)
