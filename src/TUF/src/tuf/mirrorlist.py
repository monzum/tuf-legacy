"""
<Program Name>
  mirrorlist.py

<Author>
  Konstantin Andrianov

<Started>
  October 26, 2012.

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provide helper functions to setup mirrorlist metadata.

  mirrorlist_dict corresponds to MIRRORDICT_SCHEMA.
  MIRRORDICT_SCHEMA looks like this:
    {'mirror1' : {'url_prefix' = 'http://localhost:8001',
                  'metadata_path' = 'metadata',
                  'targets_path' = 'targets',
                  'confined_target_paths' = ['']},
     'mirror2' : {'url_prefix' = 'http://localhost:8002',
                  'metadata_path' = 'metadata',
                  'targets_path' = 'targets',
                  'confined_target_paths' = ['']}, ...}

<Procedures>
  In order to modify mirrorlist metadata file:
  1. Use 'load_mirrorlist_from_file' method to populate 'mirrorlist_dict'.
  2. Use 'add_mirror' or 'remove_mirror' to modify 'mirrorlist_dict'.
  3. Use 'build_mirrorlist_file' method to write/rewrite mirrorlist.txt.

"""

import os
import shutil
import logging


import tuf.repo.signerlib
import tuf.repo.keystore
import tuf.download
import tuf.formats
import tuf.roledb
import tuf.util
import tuf.sig

# See 'log.py' to learn how logging is handled in TUF.
logger = logging.getLogger('tuf')


MAX_ATTEMPTS = 3
mirrorlist_dict = {}


def _prompt(message, result_type=str):
  """
    Prompt the user for input by printing 'message', converting
    the input to 'result_type', and returning the value to the
    caller.

  """

  return result_type(raw_input(message))





def add_mirror():
  """
  <Purpose>
    Add a mirror to mirrorlist_dict.

  <Exceptions>
    tuf.Error:
      On failure to create a mirror.
  """

  # Collecting necessary information for mirror's entry.
  for attempt in range(MAX_ATTEMPTS):
    mirror_name = _prompt('Enter mirror\'s name: ')
    tuf.formats.NAME_SCHEMA.check_match(mirror_name)
    mirror_url = _prompt('Enter mirror\'s URL: ')
    tuf.formats.URL_SCHEMA.check_match(mirror_url)

    # Make sure mirror's name and/or url are not in the dictionary already.
    if mirrorlist_dict is not None:
      for mirror in mirrorlist_dict.keys():
        if mirror == mirror_name:
          logger.warning('Mirror name: '+repr(mirror_name)+' already exists.')
          mirror_name = None
        elif mirrorlist_dict[mirror]['url_prefix'] == mirror_url:
          logger.warning('Mirror with URL: '+repr(mirror_url)+
                         ' already exists.')
          mirror_url = None
    if mirror_name is not None or mirror_url is not None:
      break

  if mirror_name is None or mirror_url is None:
    msg = ('\nYou\'ve entered '+str(MAX_ATTEMPTS)+' invalid attempts.'+
           '\nExiting...')
    raise tuf.Error(msg)

  mirrorlist_dict[mirror_name] = {}
  mirrorlist_dict[mirror_name]['url_prefix'] = mirror_url  


  metadata_dir_msg = 'Enter directory where metadata files are stored: '
  mirror_metadata_path = _prompt(metadata_dir_msg)
  tuf.formats.PATH_SCHEMA.check_match(mirror_metadata_path)
  mirrorlist_dict[mirror_name]['metadata_path'] = mirror_metadata_path


  targets_dir_msg = 'Enter directory where target files (updates) are stores: ' 
  mirror_targets_path = _prompt(targets_dir_msg)
  tuf.formats.PATH_SCHEMA.check_match(mirror_targets_path)
  mirrorlist_dict[mirror_name]['targets_path'] = mirror_targets_path

  
  mirrorlist_dict[mirror_name]['confined_target_paths'] = []
  number_confined_paths = _prompt('Enter number of confined paths: ')
  if int(number_confined_paths) <= 0:
    mirrorlist_dict[mirror_name]['confined_target_paths'].append('')

  else:
    for number in range(len(number_confined_paths)):
      confined_paths_msg = 'Enter confined path: '
      path = _prompt(confined_paths_msg)
      tuf.formats.PATH_SCHEMA.check_match(path)
      mirrorlist_dict[mirror_name]['confined_target_paths'].append(path)





def remove_mirror():
  """
  <Purpose>
    Remove a mirror from mirrorlist_dict.

  <Arguments>
    mirror_url:
      Identify a mirror to remove based on it's URL.

  <Exceptions>
    tuf.FormatError:
      On wrong format of mirror_url.
  """

  _view_mirrorlist()
  mirror_url = _prompt('Enter mirror\'s URL to remove the mirror: ')


  # Verify format of mirror_url.
  tuf.formats.URL_SCHEMA.check_match(mirror_url)

  
  for mirror_name, mirror_info in mirrorlist_dict.items():
    if mirror_url == mirror_info['url_prefix']:
      del mirrorlist_dict[mirror_name]
      print 'Successfully deleted mirror with URL '+repr(mirror_url)+\
            ' from the mirrorlist_dict dictionary.'
      return


  print 'URL '+repr(mirror_url)+' was NOT found in the mirrorlist dictionary.'





def generate_mirrorlist_metadata(mirrors_dictionary):
  """
  <Purpose>
    Generate the mirrorlist metadata object.

  <Arguments>
    mirrors_dictionary:
      A dictionary containing corresponding to MIRRORDICT_SCHEMA.

  <Exceptions>
    tuf.FormatError, if the generated timestamp metadata object could
    not be formatted correctly.

  <Side Effects>
    None.

  <Returns>
    A mirrorlist 'signable' object, conformant to 
    'tuf.formats.SIGNABLE_SCHEMA'.

  """  

  # Does 'mirrorlist_dictionary' have the correct format?
  # Raise 'tuf.FormatError' if there is a mismatch.
  #tuf.formats.MIRRORLIST_SCHEMA.check_match(mirrors_dictionary)

  
  msg = ('Do you want to add a mirror to mirrors dictionary?(y/n): ')
  another_mirror = _prompt(msg)
  while another_mirror == 'y':
    add_mirror()
    another_mirror = _prompt(msg)


  mirror_list = []
  for mirror_name, mirror_info in mirrors_dictionary.items():
    mirror_list.append(mirror_info)


  # Generate the 'mirrorlist' metadata object.
  mirrorlist_metadata = tuf.formats.MirrorsFile.make_metadata(mirror_list)
  
  return tuf.formats.make_signable(mirrorlist_metadata)





def build_mirrorlist_file(mirrors_dictionary,
                          mirrorlist_keyids,
                          metadata_directory):
  """
  <Purpose>
    Build the mirrorlist metadata file using the signing keys provided in
    'mirrorlist_keyids'.  The generated metadata file is saved in 
    'metadata_directory'.

  <Arguments>
    mirrorlist_keyids:
      The list of keyids to be used as the signing keys for the release file.

    mirrors_dictionary:
      A dictionary of mirrors that corresponds to MIRRORDICT_SCHEMA format.

    metadata_directory:
      The directory (absolute path) to save the release metadata file.

  <Exceptions>
    tuf.FormatError, if any of the arguments are improperly formatted.

    tuf.Error, if there was an error while building the mirrorlist file.

  <Side Effects>
    The mirrorlist metadata file is written to a file.

  <Returns>
    The path for the written mirrorlist metadata file.

  """

  # Do the arguments have the correct format?
  # Raise 'tuf.FormatError' if there is a mismatch.
  tuf.formats.KEYIDS_SCHEMA.check_match(mirrorlist_keyids)
  tuf.formats.PATH_SCHEMA.check_match(metadata_directory)
  
  print
  print mirrors_dictionary

  metadata_directory = tuf.repo.signerlib.check_directory(metadata_directory)

  # Generate the file path of the mirrorlist metadata.
  mirrorlist_filepath = os.path.join(metadata_directory, 'mirrorlist.txt')

  # Generate and sign the mirrorlist metadata.
  mirrorlist_metadata = generate_mirrorlist_metadata(mirrors_dictionary)
  signable = tuf.repo.signerlib.sign_metadata(mirrorlist_metadata,
                                              mirrorlist_keyids,
                                              'mirrorlist.txt')

  return tuf.repo.signerlib.write_metadata_file(signable, mirrorlist_filepath)





def load_mirrorlist_from_file(mirrorlist_filepath):
  """
  <Purpose>
    Populate mirrorlist_dict from mirrorlist (.../mirrorlist.txt) file.

  <Arguments>
    Absolute path of mirrorlist.txt file.

  <Exceptions>
    tuf.FormatError:
      On invalid format of 'mirrorlist_filepath'.

  <Side Effect>
    mirrorlist_dict is populated with mirrors.

  """

  # Verify format of 'mirrorlist_filepath'.
  tuf.formats.PATH_SCHEMA.check_match(mirrorlist_filepath)

  # Load metadata. The loaded metadata object corresponds to SIGNABLE_SCHEMA.
  mirrorlist_signable = tuf.util.load_json_file(mirrorlist_filepath)

  # Ensure the loaded json object is properly formated.
  try: 
    tuf.formats.check_signable_object_format(mirrorlist_signable)
  except tuf.FormatError, e:
    raise RepositoryError('Invalid format: '+repr(mirrorlist_filepath)+'.')

  # Extract a list of mirrors from 'mirrorlist_signable'.  The list
  # of mirrors is used to populate the 'mirrorlist_dict'.
  mirror_list = mirrorlist_signable['signed']['mirrors']
   
  mirror_count = 0
  for mirror in mirror_list:
    mirror_name = 'mirror'+str(mirror_count)
    mirrorlist_dict[mirror_name] = {}
    mirrorlist_dict[mirror_name] = mirror
    mirror_count += 1
  
  return mirrorlist_dict





def _view_mirrorlist():
  """
  <Purpose>
    To display mirrors from 'mirrorlist_dict' dictionary.

  """

  print
  for mirror_name, mirror_info in mirrorlist_dict.items():
    print '\nMirror Name: '+mirror_name
    print 'url_prefix: '+repr(mirror_info['url_prefix'])
    #print 'metadata_path: '+repr(mirror_info['metadata_path'])
    #print 'targets_path: '+repr(mirror_info['targets_path'])
    #print 'confined_target_paths: '+\
          #repr(mirror_info['confined_target_paths'])




def update_mirrorlist(url, metadata_directory):
  """
  <Purpose>
    Download and install a fresh mirrorlist metadata file from
    the server.

  <Arguments>
    url:
      Server's url where metadata file lives.

    mirrorlist_filepath:
      Location of mirrorlist.txt file.

  <Exceptions>
    tuf.FormatError
      If 'url' has an improper format.

    tuf.DownloadError
      If downloading mirrorlist metadata fails.

  """

  # Verify correct format of 'url'.
  tuf.formats.URL_SCHEMA.check_match(url)
  
  # Verify correct format of 'mirrorlist_filepath'.
  tuf.formats.PATH_SCHEMA.check_match(metadata_directory)

  current_dir = os.path.join(metadata_directory, 'current')
  previous_dir = os.path.join(metadata_directory, 'previous')
  root_filepath = os.path.join(current_dir, 'root.txt')
  mirrorlist_current_filepath = os.path.join(current_dir, 'mirrorlist.txt')
  mirrorlist_previous_filepath = os.path.join(current_dir, 'mirrorlist.txt')
  shutil.move(mirrorlist_current_filepath, mirrorlist_previous_filepath)

  # Reference to tuf.download.download_url_to_tempfileobj function.
  download_mirrorlist = tuf.download.download_url_to_tempfileobj

  try:
    mirrorlist_tempfileobj = download_mirrorlist(url)
  except tuf.DownloadError, e:
    logger.warn('Mirrorlist metadata file download failed.')
    return

  mirrorlist_signable = tuf.util.load_json_string(mirrorlist_tempfileobj.read()) 
  tuf.formats.check_signable_object_format(mirrorlist_signable)

  # In order to verify 'mirrorlist_signable' signature, the roledb
  # dictionary 'roledb_dict' has to have mirrorlist role info loaded.
  # All this, is done to retrieve mirrorlist threshold.
  # Get mirrorlist.txt file info and generate mirrorlist.
  
  root_signable = tuf.util.load_json_file(root_filepath)

  tuf.keydb.create_keydb_from_root_metadata(root_signable['signed'])
  tuf.roledb.create_roledb_from_root_metadata(root_signable['signed'])

  keyid = mirrorlist_signable['signatures'][0]['keyid']
  mirrorlist_roleinfo = {}
  mirrorlist_roleinfo['keyids'] = [keyid]
  mirrorlist_roleinfo['threshold'] = 1

  # Verify 'mirrorlist_signable' signature.
  try:
    sig_verify = tuf.sig.verify(mirrorlist_signable, 'mirrorlist')
  except (tuf.UnknownRoleError, tuf.FormatError, tuf.Error), e:
    message = 'Unable to verify mirrorlist signature:'+str(e)
    logger.warn(message)
 
  if sig_verify:
    logger.debug('Good mirrorlist signature.')
  else:
    logger.warn('Bad mirrorlist signature.')
    mirrorlist_signable = None

  # Raise an exception if a valid metadata signable could not be downloaded
  # from any of the mirrors.
  if mirrorlist_signable is None:
    raise tuf.RepositoryError('Unable to update \'mirrorlist.txt\'.')


  mirrorlist_tempfileobj.move(mirrorlist_current_filepath)
