import os
import sys
import shutil
import tempfile


import tuf.rsa_key as rsa_key
import tuf.repo.keystore as keystore
import tuf.repo.signerlib as signerlib
import tuf.repo.signercli as signercli
import tuf.tests.unittest_toolbox as unittest_toolbox




# Populating 'rsa_keystore' and 'rsa_passwords' dictionaries.
# We will need them in creating keystore directory.
TestCase_Tools = unittest_toolbox.Modified_TestCase
TestCase_Tools.bind_keys_to_roles()


def create_keystore(keystore_directory):
  if not TestCase_Tools.rsa_keystore or not TestCase_Tools.rsa_passwords:
    msg = 'Populate \'rsa_keystore\' and \'rsa_passwords\''+\
          ' before invoking this method.'
    sys.exit(msg)

  keystore._keystore = TestCase_Tools.rsa_keystore
  keystore._key_passwords = TestCase_Tools.rsa_passwords
  keystore.save_keystore_to_keyfiles(keystore_directory)





def build_server_repository(server_repository_dir, targets_dir):

  #  Make metadata directory inside client and server repository dir.
  server_metadata_dir = os.path.join(server_repository_dir, 'metadata')
  os.mkdir(server_metadata_dir)


  #  Make a keystore directory inside server's repository and populate it.
  keystore_dir = os.path.join(server_repository_dir, 'keystore')
  os.mkdir(keystore_dir)
  create_keystore(keystore_dir)


  #  Build config file.
  build_config = signerlib.build_config_file
  config_filepath = build_config(server_repository_dir, 365,
                                 TestCase_Tools.top_level_role_info)


  #  Role:keyids dictionary.
  role_keyids = {}
  for role in TestCase_Tools.semi_roledict.keys():
    role_keyids[role] = TestCase_Tools.semi_roledict[role]['keyids']



  # BUILD ROLE FILES.
  #  Build root file.
  signerlib.build_root_file(config_filepath, role_keyids['root'],
                            server_metadata_dir)

  #  Build targets file.
  signerlib.build_targets_file(targets_dir, role_keyids['targets'],
                            server_metadata_dir)

  #  Build release file.
  signerlib.build_release_file(role_keyids['release'], server_metadata_dir)

  #  Build timestamp file.
  signerlib.build_timestamp_file(role_keyids['timestamp'], server_metadata_dir)



  # MAKE DELEGATIONS.
  #  We will need to patch a few signercli prompts.
  #  Specifically, signercli.make_delegations() asks user input for:
  #  metadata directory, delegated targets directory, parent role,
  #  passwords for parent role's keyids, delegated role's name, and
  #  the keyid to be assigned to the delegated role.  Take a look at
  #  signercli's make_delegation() to gain bit more insight in what is
  #  happening.

  # 'load_key' is a reference to the 'load_keystore_from_keyfiles function'.
  load_keys = keystore.load_keystore_from_keyfiles

  #  Setup first level delegated role.
  delegated_level1 = os.path.join(targets_dir, 'delegated_level1')
  delegated_targets_dir = delegated_level1
  parent_role = 'targets'
  delegated_role_name = 'delegated_role1'
  signing_keyids = role_keyids['targets/delegated_role1'] 
  

  #  Patching the prompts.
  
  #  Mock method for signercli._get_metadata_directory().
  def _mock_get_metadata_directory():
    return server_metadata_dir

  #  Mock method for signercli._prompt().
  def _mock_prompt(msg, junk):
    if msg.startswith('\nNOTE: The directory entered'):
      return delegated_targets_dir
    elif msg.startswith('\nChoose and enter the parent'):
      return parent_role
    elif msg.endswith('\nEnter the delegated role\'s name: '):
      return delegated_role_name
    else:
      error_msg = ('Prompt: '+'\''+msg+'\''+
                   ' did not match any predefined mock prompts.')
      sys.exit(error_msg)
   
  #  Mock method for signercli._get_password().
  def _mock_get_password(msg):
    for keyid in TestCase_Tools.rsa_keyids:
      if msg.endswith('('+keyid+'): '):
        return TestCase_Tools.rsa_passwords[keyid]


  #  Method to patch signercli._get_keyids()
  def _mock_get_keyids(junk):
    if signing_keyids:
      for keyid in signing_keyids:
        password = TestCase_Tools.rsa_passwords[keyid]
        #  Load the keyfile.
        load_keys(keystore_dir, [keyid], [password])
    return signing_keyids


  #  Patch signercli._get_metadata_directory().
  signercli._get_metadata_directory = _mock_get_metadata_directory
  
  #  Patch signercli._prompt().
  signercli._prompt = _mock_prompt

  #  Patch signercli._get_password().
  signercli._get_password = _mock_get_password

  #  Patch signercli._get_keyids().
  signercli._get_keyids = _mock_get_keyids

 
  #  Clear kestore's dictionaries, by detaching them from unittest_toolbox's
  #  dictionaries.
  keystore._keystore = {}
  keystore._key_passwords = {}

  #  Make first level delegation.
  signercli.make_delegation(keystore_dir)


  #  Setup first level delegated role.
  delegated_level2 =  os.path.join(delegated_level1, 'delegated_level2')
  delegated_targets_dir = delegated_level2
  parent_role = 'targets/delegated_role1'
  delegated_role_name = 'delegated_role2'
  signing_keyids = role_keyids['targets/delegated_role1/delegated_role2']

  #  Clear kestore's dictionaries.
  keystore.clear_keystore()

  #  Make second level delegation.
  signercli.make_delegation(keystore_dir)





#  Create a complete server and client repositories.
def create_repositories():
  '''
  Main directories have the following structure:

                        main_repository
                             |
                     ------------------
                     |                |
       client_repository_dir      server_repository_dir



                      client_repository
                             |
                          metadata
                             |
                      ----------------
                      |              |
                  previous        current


                      server_repository
                             |
                 ----------------------------
                 |           |              |
             metadata     targets        keystore
                             |
                      delegation_level1
                             |
                      delegation_level2



  NOTE: Do not forget to remove the directory using remove_all_repositories
        after the tests.

  <Return>
    A dictionary of all repositories, with the following keys:
    (main_repository, client_repository, server_repository)

  '''


  #  Make a temporary general repository directory.
  repository_dir = tempfile.mkdtemp()


  #  Make server repository and client repository directories.
  server_repository_dir  = os.path.join(repository_dir, 'server_repository')
  client_repository_dir  = os.path.join(repository_dir, 'client_repository')
  os.mkdir(server_repository_dir)
  os.mkdir(client_repository_dir)


  #  Make metadata directory inside client and server repository dir.
  client_metadata_dir = os.path.join(client_repository_dir, 'metadata')
  os.mkdir(client_metadata_dir)


  #  Make current and previous directories inside metadata dir.
  current_directory = os.path.join(client_metadata_dir, 'current')
  previous_directory = os.path.join(client_metadata_dir, 'previous')
  os.mkdir(current_directory)
  os.mkdir(previous_directory)


  #  Create a project directory.
  targets = os.path.join(server_repository_dir, 'targets')
  delegated_level1 = os.path.join(targets, 'delegated_level1')
  delegated_level2 = os.path.join(delegated_level1, 'delegated_level2')
  os.makedirs(delegated_level2)

  #  Populate the project directory with some files.
  file_path_1 = tempfile.mkstemp(suffix='.txt', dir=targets)
  file_path_2 = tempfile.mkstemp(suffix='.txt', dir=targets)
  file_path_3 = tempfile.mkstemp(suffix='.txt', dir=delegated_level1)
  file_path_4 = tempfile.mkstemp(suffix='.txt', dir=delegated_level2)
  data = 'Stored data'
  file_1 = open(file_path_1[1], 'wb')
  file_1.write(data)
  file_1.close()
  file_2 = open(file_path_2[1], 'wb')
  file_2.write(data)
  file_2.close()
  file_3 = open(file_path_3[1], 'wb')
  file_3.write(data)
  file_3.close()
  file_4 = open(file_path_4[1], 'wb')
  file_4.write(data)
  file_4.close()


  #  Build server repository.
  build_server_repository(server_repository_dir, targets)

  repositories = {'main_repository': repository_dir,
                  'client_repository': client_repository_dir,
                  'server_repository': server_repository_dir}

  return repositories




#  client_repository_include_role_file() works only for top level roles.
def client_repository_include_role_file(repository_dir, role):

  client_repe = os.path.join(repository_dir, 'client_repository', 'current')
  server_repo = os.path.join(repository_dir, 'server_repository')
  root_file_path = os.path.join(server_repo, 'metadata', role+'.txt')
  shutil.copy(root_file_path, current_directory)




#  client_repository_include_all_role_files() copies all of the metadata file.
def client_repository_include_all_role_files(repository_dir):

  if repository_dir is None:
    msg = ('Please provide main rpository directory where client '+
           'repository is located.')
    sys.exit(msg)

  #  Destination directory.
  current_dir = os.path.join(repository_dir, 'client_repository', 'metadata',
                             'current')

  #  Source directory.
  metadata_files = os.path.join(repository_dir, 'server_repository',
                                'metadata')

  #  'repository_dir/metadata/curent' directory has to be removed for 
  #  shutil.copytree() to work.  The directory will be created my shutil.
  shutil.rmtree(current_dir)

  #  Copy the whole source directory to destination directory.
  shutil.copytree(metadata_files, current_dir)




#  remove_all_repositories() is a clean up method that removes all repositories.
#  Supply the main repository directory that includes all other repositories.
def remove_all_repositories(repository_directory):

  #  Check if 'repository_directory' is an existing directory.
  if os.path.isdir(repository_directory):
    shutil.rmtree(repository_directory)
  else:
    print '\nInvalid repository directory.'





if __name__ == '__main__':
  repos = create_repositories()
  client_repository_include_all_role_files(repos['main_repository'])

  remove_all_repositories(repos['main_repository'])
