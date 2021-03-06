"""
<Program Name>
  quickstart.py

<Authors>
  Original:
    Vladimir Diaz <vladimir.v.diaz@gmail.com>
  
  Modified by:
    Konstantin Andrianov


<Started>
  June 2012.  Based on a previous version by Geremy Condra.

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  This program acts as a handy quickstart for TUF, helping project and
  repository maintainers get into the game as quickly and painlessly as
  possible.  'quickstart' will create the metadata for all the top-level
  roles (along with their respective cryptographic keys), all of the
  target files specified by the user, and a configuration file named
  'config.cfg'.  The user may then use the 'signercli' script to modify,
  if they wish, the basic repository created by 'quickstart'.

  If successfully executed, 'quickstart.py' creates the 'repository',
  'keystore', and 'client' directories.  The 'repository' directory
  should be transferred to the server responding to TUF repository
  requests.  'keystore' and the individual encrypted key files should be
  securely stored and managed by the repository maintainer; these files will
  be needed again when modifying the metadata files.  And 'client' should
  be initially distributed to users by the software updater utilizing
  TUF.

<Usage>
  $ python quickstart.py --<option>

  Examples:
  $ python quickstart.py --project ./project-files/
  $ python quickstart.py --project ./project-files/ --verbose 1

<Options>
  --verbose:
    Set the verbosity level of logging messages.  Accepts values 1-5.

  --project:
    Specify the project directory containing the target files to be
    served by the TUF repository.

"""

import datetime
import getpass
import sys
import os
import optparse
import ConfigParser
import shutil
import logging

import tuf
import tuf.repo.signerlib
import tuf.repo.keystore
import tuf.formats
import tuf.util
import tuf.log
import tuf.mirrors_conf
import tuf.mirrorlist

# See 'log.py' to learn how logging is handled in TUF.
logger = logging.getLogger('tuf')

# Set the default file names for the top-level roles.
# For instance, in signerlib.py ROOT_FILENAME = 'root.txt'.
ROOT_FILENAME = tuf.repo.signerlib.ROOT_FILENAME
TARGETS_FILENAME = tuf.repo.signerlib.TARGETS_FILENAME
RELEASE_FILENAME = tuf.repo.signerlib.RELEASE_FILENAME
TIMESTAMP_FILENAME = tuf.repo.signerlib.TIMESTAMP_FILENAME

# The maximum number of attempts the user has to enter
# valid input.
MAX_INPUT_ATTEMPTS = 3


def _prompt(message, result_type=str):
  """
    Prompt the user for input by printing 'message', converting
    the input to 'result_type', and returning the value to the
    caller.

  """

  return result_type(raw_input(message))





def _get_password(prompt='Password: ', confirm=False):
  """
    Return the password entered by the user.  If 'confirm'
    is True, the user is asked to enter the previously
    entered password once again.  If they match, the
    password is returned to the caller.

  """

  while True:
    # getpass() prompts the user for a password without echoing
    # the user input.
    password = getpass.getpass(prompt, sys.stderr)
    if not confirm:
      return password
    password2 = getpass.getpass('Confirm: ', sys.stderr)
    if password == password2:
      return password
    else:
      print 'Mismatch; try again.'





def build_repository(project_directory):
  """
  <Purpose>
    Build a basic repository.  All of the required files needed of a repository
    mirror are created, such as the metadata files of the top-level roles,
    cryptographic keys, and the directories containing all of the target files.

  <Arguments>
    project_directory:
      The directory containing the target files to be copied over to the
      targets directory of the repository.

  <Exceptions>
    tuf.RepositoryError, if there was an error building the repository.

  <Side Effects>
    The repository files are written to disk to the directories specified by
    the user.

  <Returns>
    None.

  """

  mirrors_dict = tuf.mirrors_conf.mirrors

  # Do the arguments have the correct format?
  # Raise 'tuf.RepositoryError' if there is a mismatch.
  try:
    tuf.formats.PATH_SCHEMA.check_match(project_directory)
  except tuf.FormatError, e:
    message = str(e)
    raise tuf.RepositoryError(message)

  # Verify the 'project_directory' argument.
  project_directory = os.path.abspath(project_directory)
  try:
    tuf.repo.signerlib.check_directory(project_directory)
  except (tuf.FormatError, tuf.Error), e:
    message = str(e)
    raise tuf.RepositoryError(message)

  # Handle the expiration time.  The expiration date determines when
  # the top-level roles expire.
  message = '\nWhen would you like your certificates to expire? (mm/dd/yyyy): '
  timeout = None
  for attempt in range(MAX_INPUT_ATTEMPTS):
    # Get the difference between the user's entered expiration date and today's
    # date.  Convert and store the difference to total days till expiration.
    try:
      input_date = _prompt(message)
      expiration_date = datetime.datetime.strptime(input_date, '%m/%d/%Y')
      time_difference = expiration_date - datetime.datetime.now()
      timeout = time_difference.days
      if timeout < 1:
        raise ValueError
      break
    except ValueError, e:
      logger.error('Invalid expiration date entered')
      timeout = None
      continue

  # Was a valid value for 'timeout' set?
  if timeout is None:
    raise tuf.RepositoryError('Could not get a valid expiration date\n')

  # Set the keystore and repository directories.
  keystore_directory = os.path.join(os.getcwd(), 'keystore')

  # Try to create the keystore directory.
  try:
    os.mkdir(keystore_directory)
  # 'OSError' raised if the directory exists.
  except OSError, e:
    pass

  # Build the keystore and save the generated keys.
  role_info = {}
  for role in ['root', 'targets', 'release', 'timestamp', 'mirrorlist']:
    # Ensure the user inputs a valid threshold value.
    role_threshold = None
    for attempt in range(MAX_INPUT_ATTEMPTS):
      message = '\nEnter the desired threshold for the role '+repr(role)+': '

      # Check for non-integers and values less than one.
      try:
        role_threshold = _prompt(message, int)
        if not tuf.formats.THRESHOLD_SCHEMA.matches(role_threshold):
          raise ValueError
        break
      except ValueError, e:
        logger.warning('Invalid role threshold entered')
        role_threshold = None
        continue

    # Did the user input a valid threshold value?
    if role_threshold is None:
      raise tuf.RepositoryError('Could not build the keystore\n')

    # Retrieve the password(s) for 'role', generate the key(s),
    # and save them to the keystore.
    for threshold in range(role_threshold):
      message = 'Enter the password for '+repr(role)+' ('+str(threshold+1)+'): '
      password = _get_password(message)
      key = tuf.repo.signerlib.generate_and_save_rsa_key(keystore_directory,
                                                         password)
      try:
        role_info[role]['keyids'].append(key['keyid'])
      except KeyError:
        info = {'keyids': [key['keyid']], 'threshold': role_threshold}
        role_info[role] = info

  # At this point the keystore is built and the 'role_info' dictionary
  # looks something like this:
  # {'keyids : [keyid1, keyid2] , 'threshold' : 2}
  # Build the repository directories.
  metadata_directory = None
  targets_directory = None

  # Create the repository directory in the current directory, with
  # an initial name of 'repository'.  The repository maintainer
  # may opt to rename this directory and should move it elsewhere,
  # such as the webserver that will respond to TUF requests.
  repository_directory = os.path.join(os.getcwd(), 'repository')

  # Try to create the repository directory.
  try:
    os.mkdir(repository_directory)
  # 'OSError' raised if the directory exists.
  except OSError, e:
    message = 'Trying to create a new repository over an old repository '+\
      'installation.  Remove '+repr(repository_directory)+' before '+\
      'trying again.'
    raise tuf.RepositoryError(message)

  # Try to create the metadata directory that will hold all of the
  # metadata files, such as 'root.txt' and 'release.txt'.
  try:
    metadata_directory = os.path.join(repository_directory, 'metadata')
    logger.info('Creating '+repr(metadata_directory))
    os.mkdir(metadata_directory)
  except OSError, e:
    pass

  mirrorlist_info = role_info['mirrorlist']
  #del role_info['mirrorlist']

  # Build the configuration file.
  config_filepath = tuf.repo.signerlib.build_config_file(repository_directory,
                                                         timeout, role_info)
  config_fileobj = open(config_filepath, 'rb')
  print config_fileobj.read()

  # Generate the 'root.txt' metadata file.
  root_keyids = role_info['root']['keyids']
  tuf.repo.signerlib.build_root_file(config_filepath, root_keyids,
                                     metadata_directory)

  # Copy the files from the project directory to the repository's targets
  # directory.  The targets directory will hold all the individual
  # target files.
  targets_directory = os.path.join(repository_directory, 'targets')
  shutil.copytree(project_directory, targets_directory)

  # Generate the 'targets.txt' metadata file.
  targets_keyids = role_info['targets']['keyids']
  tuf.repo.signerlib.build_targets_file(targets_directory, targets_keyids,
                                        metadata_directory)

  # Generate the 'release.txt' metadata file.
  release_keyids = role_info['release']['keyids']
  tuf.repo.signerlib.build_release_file(release_keyids, metadata_directory)

  # Generate the 'timestamp.txt' metadata file.
  timestamp_keyids = role_info['timestamp']['keyids']
  tuf.repo.signerlib.build_timestamp_file(timestamp_keyids, metadata_directory)

  # Generate the 'mirrorlist.txt' metadata file.
  mirrorlist_keyids = mirrorlist_info['keyids']
  tuf.mirrorlist.build_mirrorlist_file(mirrors_dict, 
                                       mirrorlist_keyids,
                                       metadata_directory)

  # Generate the 'client' directory containing the metadata of the created
  # repository.  'tuf.client.updater.py' expects the 'current' and 'previous'
  # directories to exist under 'metadata'.
  client_metadata_directory = os.path.join(os.getcwd(), 'client', 'metadata')
  try:
    os.makedirs(client_metadata_directory)
  except OSError, e:
    message = 'Cannot create a fresh client metadata directory: '+\
      repr(client_metadata_directory)+'.  The client metadata '+\
      'will need to be manually created.  See the README file.'
    logger.warn(message)

  # Move the metadata to the client's 'current' and 'previous' directories.
  client_current = os.path.join(client_metadata_directory, 'current')
  client_previous = os.path.join(client_metadata_directory, 'previous')
  shutil.copytree(metadata_directory, client_current)
  shutil.copytree(metadata_directory, client_previous)





def parse_options():
  """
  <Purpose>
    Parse the command-line options and set the logging level
    as specified by the user using the '--verbose' option.
    The user should also set '--project' option.  If unset
    the current directory will be used as the project files.

  <Arguments>
    None.

  <Exceptions>
    None.

  <Side Effects>
    Sets the logging level for TUF logging.

  <Returns>
    The 'options.PROJECT_DIRECTORY' string.

  """

  parser = optparse.OptionParser()

  # Add the options supported by 'quickstart' to the option parser.
  parser.add_option('--verbose', dest='VERBOSE', type=int, default=3,
                    help='Set the verbosity level of logging messages.'
                         'The lower the setting, the greater the verbosity.')

  parser.add_option('--project', dest='PROJECT_DIRECTORY', type='string',
                    default='.', help='Identify the directory containing the '
                    'project files to host on the TUF repository.')

  options, args = parser.parse_args()

  # Set the logging level.
  if options.VERBOSE == 5:
    tuf.log.set_log_level(logging.CRITICAL)
  elif options.VERBOSE == 4:
    tuf.log.set_log_level(logging.ERROR)
  elif options.VERBOSE == 3:
    tuf.log.set_log_level(logging.WARNING)
  elif options.VERBOSE == 2:
    tuf.log.set_log_level(logging.INFO)
  elif options.VERBOSE == 1:
    tuf.log.set_log_level(logging.DEBUG)
  else:
    tuf.log.set_log_level(logging.NOTSET)

  # Return the directory containing the project files.  These files
  # will be copied over to the targets directory of the repository.
  return options.PROJECT_DIRECTORY



if __name__ == '__main__':

  # Parse the options and set the logging level.
  project_directory = parse_options()

  # Build the repository.  The top-level metadata files, cryptographic keys,
  # target files, and the configuration file are created.
  try:
    build_repository(project_directory)
  except tuf.RepositoryError, e:
    sys.stderr.write(str(e)+'\n')
    sys.exit(1)

  print '\nSuccessfully created the repository.'
  sys.exit(0)
