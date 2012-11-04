"""
<Program Name>
  test_signercli.py

<Author>
  Konstantin Andrianov

<Started>
  September 20, 2012

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  test_signercli.py provides collection of methods that tries to test all the
  units (methods) of the module under test.

  unittest_toolbox module was created to provide additional testing tools for
  tuf's modules.  For more info see unittest_toolbox.py.


<Methodology>
  Unittests must follow a specific structure i.e. independent methods should
  be tested prior to dependent methods. More accurately: least dependent
  methods are tested before most dependent methods.  There is no reason to
  rewrite or construct other methods that replicate already-tested methods
  solely for testing purposes.  This is possible because 'unittest.TestCase'
  class guarantees the order of unit tests.  So that, 'test_something_A'
  method would be tested before 'test_something_B'.  To ensure the structure
  a number will be placed after 'test' and before methods name like so:
  'test_1_check_directory'.  The number is a measure of dependence, where 1
  is less dependent than 2.


"""


import os

import tuf.util
import tuf.repo.keystore as keystore
import tuf.repo.signerlib as signerlib
#  Module to test: signercli.py
import tuf.repo.signercli as signercli
#  Helper module unittest_toolbox.py
import tuf.tests.unittest_toolbox as unittest_toolbox



# Populating 'rsa_keystore' and 'rsa_passwords' dictionaries.
# We will need them in creating keystore directory.
unittest_toolbox.Modified_TestCase.bind_keys_to_roles()



class TestSignercli(unittest_toolbox.Modified_TestCase):


  #  HELPER METHODS.

  #  Generic patch for signerlib._prompt().
  def mock_prompt(self, output):

    #  Method to patch signercli._prompt().
    def _mock_prompt(junk1, junk2, ret=output):
      return ret

    #  Patch signercli._prompt()
    signercli._prompt = _mock_prompt



  #  Patch signercli._get_metadata_directory()
  def mock_get_metadata_directory(self, directory=None):

    #  Create method to patch signercli._get_metadata_directory()
    def _mock_get_meta_dir(directory=directory):

      #  If directory was specified, return that directory.
      if directory:
        return directory

      #  Else create a temporary directory and return it.
      else:
        return self.make_temp_directory()

    #  Patch signercli._get_metadata_directory()
    signercli._get_metadata_directory = _mock_get_meta_dir



  #  This method patches signercli._prompt() that are called from
  #  make_role_metadata methods (e.g., tuf.signercli.make_root_metadata()).
  def make_metadata_mock_prompts(self, targ_dir, conf_path):
    def _mock_prompt(msg, junk):
      if msg.startswith('\nEnter the directory containing the target'):
        return targ_dir
      elif msg.startswith('\nEnter the configuration file path'):
        return conf_path
      else:
        error_msg = ('Prompt: '+'\''+msg[1:]+'\''+
            ' did not match any predefined mock prompts.')
        self.fail(error_msg)

    #  Patch signercli._prompt().
    signercli._prompt = _mock_prompt



  #  This mock method can be easily modified, by altering unittest_toolbox's
  #  dictionaries.  For instance, if you want to modify password for certain
  #  keyid just save the existing 'self.rsa_passwords[keyid]' and set it
  #  to some other value like self.random_string(), after the test reassign
  #  the saved value back to 'self.rsa_passwords[keyid]'.
  def get_passwords(self):

    #  Mock '_get_password' method.
    def _mock_get_password(msg):
      for role in self.role_list:
        if msg.startswith('\nEnter the password for the '+role):
          for keyid in self.semi_roledict[role]['keyids']:
            if msg.endswith(keyid+'): '):
              return self.rsa_passwords[keyid]
      error_msg = ('Prompt: '+'\''+msg+'\''+
          ' did not match any predefined mock prompts.')
      raise tuf.Error(error_msg)

    #  Monkey patch '_prompt'.
    signercli._get_password = _mock_get_password





  #  UNIT TESTS.
  #  If a unit test starts with test_# followed by two underscores,
  #  (test_#__method) this means that it's an internal method of signercli.
  #  For instance the unit test for signercli._get_password() would
  #  look like this: test_1__get_password, whereas unit test for
  #  signercli.change_password would look like this:
  #  test_3_change_password().

  def test_1__check_directory(self):

    # SETUP
    directory = self.make_temp_directory()
    no_such_dir = self.random_path()


    # TESTS
    #  Test: normal case.
    self.assertEqual(signercli._check_directory(directory), directory)


    #  Test: invalid directory.
    self.assertRaises(tuf.RepositoryError, signercli._check_directory,
        no_such_dir)


    #  Test: invalid directory type.
    self.assertRaises(tuf.RepositoryError, signercli._check_directory,
                      [no_such_dir])
    self.assertRaises(tuf.RepositoryError, signercli._check_directory,
                      1234)
    self.assertRaises(tuf.RepositoryError, signercli._check_directory,
                      {'directory':no_such_dir})





  def test_1__get_password(self):

    # SETUP
    password = self.random_string()
    def _mock_getpass(junk1, junk2, pw=password):
      return pw

    # Patch getpass.getpass().
    signercli.getpass.getpass = _mock_getpass


    # Test: normal case.
    self.assertEqual(signercli._get_password(), password)





  def test_2__get_metadata_directory(self):

    # SETUP
    meta_directory = self.make_temp_directory()
    self.mock_prompt(meta_directory)



    # TESTS
    self.assertEqual(signercli._get_metadata_directory(), meta_directory)
    self.assertTrue(os.path.exists(signercli._get_metadata_directory()))
    self.mock_prompt(self.random_string())
    self.assertRaises(tuf.RepositoryError, signercli._get_metadata_directory)
    self.mock_prompt([self.random_string()])
    self.assertRaises(tuf.RepositoryError, signercli._get_metadata_directory)





  def test_1__list_keyids(self):

    # SETUP
    keystore_dir = self.create_temp_keystore_directory()


    # TESTS
    #  Test: normal case.
    try:
      signercli._list_keyids(keystore_dir)
    except Exception, e:
      self.fail(str(e))





  def test_2__get_keyids(self):
    
    # SETUP    
    #  Create a temp keystore directory.
    keystore_dir = self.create_temp_keystore_directory()

    #  List of keyids including keyword 'quit'.
    keyids = ['quit'] + self.rsa_keyids


    #  Patching signercli._prompt()
    def _mock_prompt(msg, junk):

      #  Pop 'keyids' everytime signercli._prompt() is called.
      keyid = keyids.pop()
      if keyid != 'quit':
        get_password(keyid)
      return keyid

    signercli._prompt = _mock_prompt
    

    #  Pathching signercli._get_password().
    def get_password(keyid):
      password = self.rsa_passwords[keyid]
      def _mock_get_password(msg):
        return password

      signercli._get_password = _mock_get_password



    # TESTS
    #  Test: normal case.
    try:
      loaded_keyids = signercli._get_keyids(keystore_dir)
    except Exception, e:
      raise

    #  Check if all the keysids were loaded.
    for keyid in self.rsa_keyids:
      if keyid not in loaded_keyids:
        msg = '\nCould not load the keyid: '+repr(keyid)
        self.fail(msg)
   
   
    #  Test: invalid password.
    keyids = ['quit', self.rsa_keyids[0]]
    saved_pw = self.rsa_passwords[keyid]
    
    #  Invalid password
    self.rsa_passwords[self.rsa_keyids[0]] = self.random_string()
    self.assertEqual(signercli._get_keyids(keystore_dir), [])

    #  Restore the password.
    self.rsa_passwords[self.rsa_keyids[0]] = saved_pw


    #  Test: invalid keyid.
    keyid = self.random_string()
    keyids = ['quit', keyid]

    #  Create an entry in the passwords dictionary.
    self.rsa_passwords[keyid] = self.random_string()
    self.assertEqual(signercli._get_keyids(keystore_dir), [])

    #  Restore passwords dictionary.
    del self.rsa_passwords[keyid]





  def test_2__get_all_config_keyids(self):

    # SETUP
    #  Create temp directory for config file.
    config_dir = self.make_temp_directory()

    #  Build config file.
    config_filepath = signerlib.build_config_file(config_dir, 365,
                                                  self.semi_roledict)

    #  Create a temp keystore directory.
    keystore_dir = self.create_temp_keystore_directory()

    #  'sample_keyid' used to test invalid keyid.
    sample_keyid = self.rsa_keyids[0]

    #  Patch signercli._get_password()
    self.get_passwords()



    # TESTS
    #  Test: an incorrect password.
    saved_pw = self.rsa_passwords[sample_keyid]
    self.rsa_passwords[sample_keyid] = self.random_string()
    self.assertRaises(tuf.Error, signercli._get_all_config_keyids,
                      config_filepath, keystore_dir)

    #  Restore the password.
    self.rsa_passwords[sample_keyid] = saved_pw


    #  Test: missing top-level role in the config file.
    #    Clear keystore's dictionaries.
    keystore.clear_keystore()

    #    Remove a role from 'semi_roledict' which is used to construct
    #    config file.
    self.semi_roledict['targets_holder'] = self.semi_roledict['targets']
    del self.semi_roledict['targets']

    #    Build config file without 'targets' role.
    config_filepath = signerlib.build_config_file(config_dir, 365,
                                                  self.semi_roledict)
    self.assertRaises(tuf.Error, signercli._get_all_config_keyids,
                      config_filepath, keystore_dir)

    #    Rebuild config file and 'semi_roledict'.
    self.semi_roledict['targets'] = self.semi_roledict['targets_holder']
    del self.semi_roledict['targets_holder']
    config_filepath = signerlib.build_config_file(config_dir, 365,
                                                  self.semi_roledict)


    #  Test: non-existing config file path.
    keystore.clear_keystore()
    self.assertRaises(tuf.Error, signercli._get_all_config_keyids,
                      self.random_path(), keystore_dir)


    #  Test: normal case.
    keystore.clear_keystore()
    try:
      signercli._get_all_config_keyids(config_filepath, keystore_dir)
    except Exception, e:
      self.fail(str(e))





  def test_2__get_role_config_keyids(self):

    # SETUP
    #  Create temp directory for config file.
    config_dir = self.make_temp_directory()

    #  Build a config file.
    config_filepath = signerlib.build_config_file(config_dir, 365,
                                                  self.semi_roledict)
    #  Create a temp keystore directory.
    keystore_dir = self.create_temp_keystore_directory()

    #  Patch '_get_password' method.
    self.get_passwords()



    # TESTS
    for role in self.role_list:

      #  Test: normal cases.
      keystore.clear_keystore()
      try:
        signercli._get_role_config_keyids(config_filepath,
            keystore_dir, role)
      except Exception, e:
        self.fail(str(e))
      
      #  Test: incorrect passwords.
      keystore.clear_keystore()
      role_keyids = self.semi_roledict[role]['keyids']
      for keyid in role_keyids:
        saved_pw = self.rsa_passwords[keyid]
        self.rsa_passwords[keyid] = self.random_string()
        self.assertRaises(tuf.Error, signercli._get_role_config_keyids,
            config_filepath, keystore_dir, role)

        #    Restore the password.
        self.rsa_passwords[keyid] = saved_pw


    #  Test: non-existing config file path.
    keystore.clear_keystore()
    self.assertRaises(tuf.Error, signercli._get_role_config_keyids,
        self.random_path(), keystore_dir, 'release')


    #  Test: non-existing role.
    keystore.clear_keystore()
    self.assertRaises(tuf.Error, signercli._get_role_config_keyids,
                      config_filepath, keystore_dir, 'no_such_role')





  def test_1__sign_and_write_metadata(self):

    # SETUP
    #  Role to test.
    role = 'root'

    #  Create temp directory.
    temp_dir = self.make_temp_directory()

    #  File name.
    filename = os.path.join(temp_dir, role+'.txt')

    #  Role's keyids.
    keyids = self.semi_roledict[role]['keyids']

    #  Create a temp keystore directory.
    keystore_dir =\
        self.create_temp_keystore_directory(keystore_dicts=True)

    #  Create temp directory for config file.
    config_dir = self.make_temp_directory()

    #  Build config file.
    config_filepath = signerlib.build_config_file(config_dir, 365,
                                                  self.semi_roledict)

    #  Create role's metadata.
    signable_meta = signerlib.generate_root_metadata(config_filepath)



    # TESTS
    #  Test: normal case.
    try:
      signercli._sign_and_write_metadata(signable_meta, keyids, filename)
    except Exception, e:
      self.fail(str(e))

    #  Verify that the root meta file was created.
    self.assertTrue(os.path.exists(filename))


    Errors = (tuf.Error, tuf.FormatError)

    #  Test: invalid metadata.
    self.assertRaises(Errors, signercli._sign_and_write_metadata,
                      self.random_string(), keyids, filename)


    #  Test: invalid keyids
    invalid_keyids = self.random_string()
    self.assertRaises(Errors, signercli._sign_and_write_metadata,
                      signable_meta, invalid_keyids, filename)

    #  Test: invalid filename
    self.assertRaises(Errors, signercli._sign_and_write_metadata,
                      signable_meta, invalid_keyids, True)




  def test_2_change_password(self):

    # SETUP
    test_keyid = self.rsa_keyids[0]
    self.mock_prompt(test_keyid)

    #  Create keystore directory.
    keystore_dir = self.create_temp_keystore_directory()

    #  Specify old password and create a new password.
    old_password = self.rsa_passwords[test_keyid]
    new_password = self.random_string()

    #  Mock method for signercli._get_password()
    def _mock_get_password(msg, confirm=False, old_pw=old_password,
        new_pw=new_password):
      if msg.startswith('\nEnter the old password for the keyid: '):
        return old_pw
      else:
        return new_pw

    #  Patch signercli._get_password.
    signercli._get_password = _mock_get_password



    # TESTS
    #  Test: normal case.
    try:
      signercli.change_password(keystore_dir)
    except Exception, e:
      self.fail(str(e))

    #  Verify password change.
    self.assertEqual(keystore._key_passwords[test_keyid], new_password)


    #  Test: non-existing keyid.
    keystore.clear_keystore()
    self.mock_prompt(self.random_string(15))
    self.assertRaises(tuf.RepositoryError, signercli.change_password,
                      keystore_dir)

    #  Restore the prompt input to existing keyid.
    self.mock_prompt(test_keyid)


    #  Test: non-existing old password.
    keystore.clear_keystore()
    old_password = self.random_string()
    self.assertRaises(tuf.RepositoryError, signercli.change_password,
                      keystore_dir)





  def test_2_generate_rsa_key(self):

    # SETUP
    #  Method to patch signercli._get_password()
    def _mock_get_password(junk, confirm=False):
      return self.random_string()

    #  Patch signercli._get_password()
    signercli._get_password = _mock_get_password

    #  Create a temp keystore directory.
    keystore_dir = self.make_temp_directory()



    # TESTS
    #  Test: invalid rsa bits.
    self.mock_prompt(1024)
    self.assertRaises(tuf.RepositoryError, signercli.generate_rsa_key,
                      keystore_dir)
    #  Input appropriate number of rsa bits.
    self.mock_prompt(3072)


    #  Test: normal case.
    try:
      signercli.generate_rsa_key(keystore_dir)
    except Exception, e:
      self.fail(str(e))

    #  Was the key file added to the directory?
    self.assertTrue(os.listdir(keystore_dir))





  #  This method just prints keyids.
  def test_3_list_signing_keys(self):
    pass





  def test_2_dump_key(self):

    # SETUP
    keyid = self.rsa_keyids[0]
    password = self.rsa_passwords[keyid]
    show_priv = 'private'


    #  Mock method for signercli._get_password().
    def _mock_get_password(msg):
      return password


    #  Mock method for signercli._prompt().
    def _mock_prompt(msg, junk):
       if msg.startswith('\nEnter the keyid'):
         return keyid
       else:
         return show_priv


    #  Patch signercli._get_password().
    signercli._get_password = _mock_get_password

    #  Patch signercli._prompt().
    signercli._prompt = _mock_prompt

    #  Create keystore directory.
    keystore_dir = self.create_temp_keystore_directory()



    # TESTS
    #  Test: normal case.
    try:
      signercli.dump_key(keystore_dir)
    except Exception, e:
      self.fail(str(e))


    #  Test: incorrect password.
    saved_pw = password
    password = self.random_string()
    self.assertRaises(tuf.RepositoryError, signercli.dump_key,
                      keystore_dir)

    #  Restore the correct password.
    password = saved_pw


    #  Test: non-existing keyid.
    keyid = self.random_string()
    self.assertRaises(tuf.RepositoryError, signercli.dump_key,
                      keystore_dir)
    keyid = self.rsa_keyids[0]





  def test_3_make_root_metadata(self):

    # SETUP
    #  Create temp directory for config file.
    config_dir = self.make_temp_directory()

    #  Build a config file.
    config_filepath = signerlib.build_config_file(config_dir, 365,
        self.semi_roledict)

    #  Create a temp metadata directory.
    meta_dir = self.make_temp_directory()

    #  Patch signercli._get_metadata_directory().
    self.mock_get_metadata_directory(directory=meta_dir)

    #  Patch signercli._prompt().
    self.mock_prompt(config_filepath)

    #  Patch signercli._get_password().
    self.get_passwords()

    #  Create keystore directory.
    keystore_dir = self.create_temp_keystore_directory()



    # TESTS
    #  Test: normal case.
    try:
      signercli.make_root_metadata(keystore_dir)
    except Exception, e:
      self.fail(str(e))

    #  Verify that the root metadata path was created.
    self.assertTrue(os.path.exists(os.path.join(meta_dir, 'root.txt')))


    #  Test: invalid config path.
    #  Clear keystore's dictionaries.
    keystore.clear_keystore()

    #  Supply a non-existing path to signercli._prompt().
    self.mock_prompt(self.random_path())
    self.assertRaises(tuf.RepositoryError, signercli.make_root_metadata,
                      keystore_dir)

    #  Re-patch signercli._prompt() with valid config path.
    self.mock_prompt(config_filepath)


    #  Test: incorrect 'root' passwords.
    #  Clear keystore's dictionaries.
    keystore.clear_keystore()
    keyids = self.semi_roledict['root']['keyids']
    for keyid in keyids:
      saved_pw = self.rsa_passwords[keyid]
      self.rsa_passwords[keyid] = self.random_string()
      self.assertRaises(tuf.RepositoryError, signercli.make_root_metadata,
                        keystore_dir)
      self.rsa_passwords[keyid] = saved_pw





  def test_3_make_targets_metadata(self):

    # SETUP
    #  Create a temp repository and metadata directories.
    repo_dir = self.make_temp_directory()
    meta_dir = self.make_temp_directory(directory=repo_dir)

    #  Create a directory containing target files.
    targets_dir, targets_paths =\
        self.make_temp_directory_with_data_files(directory=repo_dir)

    #  Create temp directory for config file.
    config_dir = self.make_temp_directory()

    #  Build a config file.
    config_filepath = signerlib.build_config_file(config_dir, 365,
                                                  self.semi_roledict)

    #  Patch signercli._get_metadata_directory()
    self.mock_get_metadata_directory(directory=meta_dir)

    #  Patch signercli._get_password().  Used in _get_role_config_keyids()
    self.get_passwords()

    #  Create keystore directory.
    keystore_dir = self.create_temp_keystore_directory()

    #  Mock method for signercli._prompt().
    self.make_metadata_mock_prompts(targ_dir=targets_dir,
                                    conf_path=config_filepath)



    # TESTS
    #  Test: normal case.
    try:
      signercli.make_targets_metadata(keystore_dir)
    except Exception, e:
      self.fail(str(e))

    #  Verify that targets metadata file was created.
    self.assertTrue(os.path.exists(os.path.join(meta_dir, 'targets.txt')))


    #  Test: invalid targets path.
    #  Clear keystore's dictionaries.
    keystore.clear_keystore()

    #  Supply a non-existing targets directory.
    self.make_metadata_mock_prompts(targ_dir=self.random_path(),
                                    conf_path=config_filepath)
    self.assertRaises(tuf.RepositoryError, signercli.make_targets_metadata,
                      keystore_dir)

    #  Restore the targets directory.
    self.make_metadata_mock_prompts(targ_dir=targets_dir,
                                    conf_path=config_filepath)


    #  Test: invalid config path.
    #  Clear keystore's dictionaries.
    keystore.clear_keystore()

    #  Supply a non-existing config path.
    self.make_metadata_mock_prompts(targ_dir=targets_dir,
                                    conf_path=self.random_path())
    self.assertRaises(tuf.RepositoryError, signercli.make_targets_metadata,
                      keystore_dir)

    #  Restore the config file path.
    self.make_metadata_mock_prompts(targ_dir=targets_dir,
                                    conf_path=config_filepath)


    #  Test: incorrect 'targets' passwords.
    #  Clear keystore's dictionaries.
    keystore.clear_keystore()
    keyids = self.semi_roledict['targets']['keyids']
    for keyid in keyids:
      saved_pw = self.rsa_passwords[keyid]
      self.rsa_passwords[keyid] = self.random_string()
      self.assertRaises(tuf.RepositoryError, signercli.make_targets_metadata,
                        keystore_dir)
      self.rsa_passwords[keyid] = saved_pw





  def test_4_make_release_metadata(self):

    #  In order to build release metadata file (release.txt),
    #  root and targets metadata files (root.txt, targets.txt)
    #  must exist in the metadata directory.

    # SETUP
    #  Create temp directory for config file.
    config_dir = self.make_temp_directory()

    #  Build a config file.
    config_filepath = signerlib.build_config_file(config_dir, 365,
                                                  self.semi_roledict)

    #  Create a temp repository and metadata directories.
    repo_dir = self.make_temp_directory()
    meta_dir = self.make_temp_directory(repo_dir)

    #  Create a directory containing target files.
    targets_dir, targets_paths = \
        self.make_temp_directory_with_data_files(directory=repo_dir)

    #  Patch signercli._get_metadata_directory().
    self.mock_get_metadata_directory(directory=meta_dir)

    #  Patch signercli._get_password().  Used in _get_role_config_keyids().
    self.get_passwords()

    #  Create keystore directory.
    keystore_dir = self.create_temp_keystore_directory()

    #  Mock method for signercli._prompt().
    self.make_metadata_mock_prompts(targ_dir=targets_dir,
                                    conf_path=config_filepath)



    # TESTS
    #  Test: no root.txt in the metadata dir.
    try:
      signercli.make_targets_metadata(keystore_dir)
    except Exception, e:
      self.fail(str(e))

    #  Verify that 'tuf.RepositoryError' is raised due to a missing root.txt.
    keystore.clear_keystore()
    self.assertTrue(os.path.exists(os.path.join(meta_dir, 'targets.txt')))
    self.assertRaises(tuf.RepositoryError, signercli.make_release_metadata,
                      keystore_dir)
    os.remove(os.path.join(meta_dir,'targets.txt'))
    keystore.clear_keystore()


    #  Test: no targets.txt in the metadatadir.
    try:
      signercli.make_root_metadata(keystore_dir)
      keystore.clear_keystore()
    except Exception, e:
      self.fail(str(e))

    #  Verify that 'tuf.RepositoryError' is raised due to a missing targets.txt.
    self.assertTrue(os.path.exists(os.path.join(meta_dir, 'root.txt')))
    self.assertRaises(tuf.RepositoryError, signercli.make_release_metadata,
                      keystore_dir)
    os.remove(os.path.join(meta_dir,'root.txt'))
    keystore.clear_keystore()


    #  Test: normal case.
    try:
      signercli.make_root_metadata(keystore_dir)
      keystore.clear_keystore()
      signercli.make_targets_metadata(keystore_dir)
      keystore.clear_keystore()
      signercli.make_release_metadata(keystore_dir)
      keystore.clear_keystore()
    except Exception, e:
      self.fail(str(e))

    #  Verify if the root, targets and release meta files were created.
    self.assertTrue(os.path.exists(os.path.join(meta_dir, 'root.txt')))
    self.assertTrue(os.path.exists(os.path.join(meta_dir, 'targets.txt')))
    self.assertTrue(os.path.exists(os.path.join(meta_dir, 'release.txt')))


    #  Test: invalid config path.
    #  Supply a non-existing config file path.
    self.make_metadata_mock_prompts(targ_dir=targets_dir,
        conf_path=self.random_path())
    self.assertRaises(tuf.RepositoryError, signercli.make_release_metadata,
        keystore_dir)

    #  Restore the config file path.
    self.make_metadata_mock_prompts(targ_dir=targets_dir,
        conf_path=config_filepath)


    #  Test: incorrect 'release' passwords.
    #  Clear keystore's dictionaries.
    keystore.clear_keystore()
    keyids = self.semi_roledict['release']['keyids']
    for keyid in keyids:
      saved_pw = self.rsa_passwords[keyid]
      self.rsa_passwords[keyid] = self.random_string()
      self.assertRaises(tuf.RepositoryError, signercli.make_release_metadata,
          keystore_dir)
      self.rsa_passwords[keyid] = saved_pw





  def test_5_make_timestamp_metadata(self):


    #  In order to build timestamp metadata file (timestamp.txt),
    #  root, targets and release metadata files (root.txt, targets.txt
    #  release.txt) must exist in the metadata directory.

    # SETUP
    #  Create temp directory for config file.
    config_dir = self.make_temp_directory()

    #  Build a config file.
    config_filepath = signerlib.build_config_file(config_dir, 365,
                                                  self.semi_roledict)

    #  Create a temp repository and metadata directories.
    repo_dir = self.make_temp_directory()
    meta_dir = self.make_temp_directory(repo_dir)

    #  Create a directory containing target files.
    targets_dir, targets_paths = \
        self.make_temp_directory_with_data_files(directory=repo_dir)

    #  Patch signercli._get_metadata_directory().
    self.mock_get_metadata_directory(directory=meta_dir)

    #  Patch signercli._get_password().  Used in _get_role_config_keyids().
    self.get_passwords()

    #  Create keystore directory.
    keystore_dir = self.create_temp_keystore_directory()

    #  Mock method for signercli._prompt().
    self.make_metadata_mock_prompts(targ_dir=targets_dir,
                                    conf_path=config_filepath)



    # TESTS
    #  Test: no root.txt in the metadata dir.
    try:
      signercli.make_targets_metadata(keystore_dir)
    except Exception, e:
      self.fail(str(e))

    #  Verify if the targets metadata file was created.
    keystore.clear_keystore()
    self.assertTrue(os.path.exists(os.path.join(meta_dir, 'targets.txt')))
    self.assertRaises(tuf.RepositoryError, signercli.make_timestamp_metadata,
                      keystore_dir)
    os.remove(os.path.join(meta_dir,'targets.txt'))
    keystore.clear_keystore()


    #  Test: no targets.txt in the metadatadir.
    try:
      signercli.make_root_metadata(keystore_dir)
    except Exception, e:
      self.fail(str(e))

    #  Verify if the root metadata file was created.
    keystore.clear_keystore()
    self.assertTrue(os.path.exists(os.path.join(meta_dir, 'root.txt')))
    self.assertRaises(tuf.RepositoryError, signercli.make_timestamp_metadata,
                      keystore_dir)
    os.remove(os.path.join(meta_dir,'root.txt'))
    keystore.clear_keystore()


    #  Test: no release.txt in the metadatadir.
    try:
      signercli.make_root_metadata(keystore_dir)
      keystore.clear_keystore()
      signercli.make_targets_metadata(keystore_dir)
      keystore.clear_keystore()
    except Exception, e:
      self.fail(str(e))

    #  Verify that 'tuf.Repository' is raised due to a missing release.txt.
    self.assertTrue(os.path.exists(os.path.join(meta_dir, 'root.txt')))
    self.assertTrue(os.path.exists(os.path.join(meta_dir, 'targets.txt')))
    self.assertRaises(tuf.RepositoryError, signercli.make_timestamp_metadata,
                      keystore_dir)
    os.remove(os.path.join(meta_dir,'root.txt'))
    os.remove(os.path.join(meta_dir,'targets.txt'))
    keystore.clear_keystore()


    #  Test: normal case.
    try:
      signercli.make_root_metadata(keystore_dir)
      keystore.clear_keystore()
      signercli.make_targets_metadata(keystore_dir)
      keystore.clear_keystore()
      signercli.make_release_metadata(keystore_dir)
      keystore.clear_keystore()
      signercli.make_timestamp_metadata(keystore_dir)
      keystore.clear_keystore()
    except Exception, e:
      self.fail(str(e))

    #  Verify if the root, targets and release metadata files were created.
    self.assertTrue(os.path.exists(os.path.join(meta_dir, 'root.txt')))
    self.assertTrue(os.path.exists(os.path.join(meta_dir, 'targets.txt')))
    self.assertTrue(os.path.exists(os.path.join(meta_dir, 'release.txt')))
    self.assertTrue(os.path.exists(os.path.join(meta_dir, 'timestamp.txt')))


    #  Test: invalid config path.
    #  Supply a non-existing config file path.
    self.make_metadata_mock_prompts(targ_dir=targets_dir,
                                    conf_path=self.random_path())
    self.assertRaises(tuf.RepositoryError,
                      signercli.make_release_metadata, keystore_dir)

    #  Restore the config file path.
    self.make_metadata_mock_prompts(targ_dir=targets_dir,
                                    conf_path=config_filepath)


    #  Test: incorrect 'release' passwords.

    #  Clear keystore's dictionaries.
    keystore.clear_keystore()

    keyids = self.semi_roledict['release']['keyids']
    for keyid in keyids:
      saved_pw = self.rsa_passwords[keyid]
      self.rsa_passwords[keyid] = self.random_string()
      self.assertRaises(tuf.RepositoryError,
                        signercli.make_release_metadata, keystore_dir)
      self.rsa_passwords[keyid] = saved_pw





  def test_6_sign_metadata_file(self):

    #  To test this method, an RSA key will be created with
    #  a password in addition to the existing RSA keys.

    # SETUP
    #  Create temp directory for config file.
    config_dir = self.make_temp_directory()

    #  Build a config file.
    config_filepath = signerlib.build_config_file(config_dir, 365,
                                                  self.semi_roledict)

    #  Create a temp repository and metadata directories.
    repo_dir = self.make_temp_directory()
    meta_dir = self.make_temp_directory(repo_dir)

    #  Create a directory containing target files.
    targets_dir, targets_paths = \
        self.make_temp_directory_with_data_files(directory=repo_dir)

    #  Patch signercli._get_metadata_directory().
    self.mock_get_metadata_directory(directory=meta_dir)

    #  Patch signercli._get_password().  Used in _get_role_config_keyids().
    self.get_passwords()

    #  Create keystore directory.
    keystore_dir = self.create_temp_keystore_directory()

    #  Mock method for signercli._prompt().
    self.make_metadata_mock_prompts(targ_dir=targets_dir,
                                    conf_path=config_filepath)

    #  Create metadata files.
    try:
      signercli.make_root_metadata(keystore_dir)
      keystore.clear_keystore()
      signercli.make_targets_metadata(keystore_dir)
      keystore.clear_keystore()
      signercli.make_release_metadata(keystore_dir)
      keystore.clear_keystore()
      signercli.make_timestamp_metadata(keystore_dir)
      keystore.clear_keystore()
    except Exception, e:
      self.fail(str(e))

    #  Verify if the root, targets and release meta files were created.
    root_meta_filepath = os.path.join(meta_dir, 'root.txt')
    targets_meta_filepath = os.path.join(meta_dir, 'targets.txt')
    release_meta_filepath = os.path.join(meta_dir, 'release.txt')
    timestamp_meta_filepath = os.path.join(meta_dir, 'timestamp.txt')

    self.assertTrue(os.path.exists(root_meta_filepath))
    self.assertTrue(os.path.exists(targets_meta_filepath))
    self.assertTrue(os.path.exists(release_meta_filepath))
    self.assertTrue(os.path.exists(timestamp_meta_filepath))


    #  Create a new RSA key, indicate metadata filename.
    new_keyid = self.generate_rsakey()
    meta_filename = targets_meta_filepath

    #  Create keystore directory.  New key is untouched.
    keystore_dir = self.create_temp_keystore_directory(keystore_dicts=True)

    #  List of keyids to be returned by _get_keyids()
    signing_keyids = []


    #  Method to patch signercli._get_keyids()
    def _mock_get_keyids(junk):
      return signing_keyids


    #  Method to patch signercli._prompt().
    def _mock_prompt(msg, junk):
      return meta_filename


    #  Patch signercli._get_keyids()
    signercli._get_keyids = _mock_get_keyids

    #  Patch signercli._prompt().
    signercli._prompt = _mock_prompt



    # TESTS
    #  Test: no loaded keyids.
    self.assertRaises(tuf.RepositoryError,
                      signercli.sign_metadata_file, keystore_dir)

    #  Load new keyid.
    signing_keyids = [new_keyid]


    #  Test: normal case.
    try:
      signercli.sign_metadata_file(keystore_dir)
    except Exception, e:
      self.fail(str(e))

    #  Verify the change.
    self.assertTrue(os.path.exists(targets_meta_filepath))

    #  Load targets metadata from the file ('targets.txt').
    targets_metadata = tuf.util.load_json_file(targets_meta_filepath)
    keyid_exists = False
    for signature in targets_metadata['signatures']:
      if new_keyid == signature['keyid']:
        keyid_exists = True
        break

    self.assertTrue(keyid_exists)





  def test_7_make_delegation(self):
    # SETUP
    #  Create a temp repository and metadata directories.
    repo_dir = self.make_temp_directory()
    meta_dir = self.make_temp_directory(directory=repo_dir)

    #  Create targets directories.
    targets_dir, targets_paths =\
        self.make_temp_directory_with_data_files(directory=repo_dir)
    delegated_targets_dir = os.path.join(targets_dir,'targets',
                                         'delegated_level1')

    #  Assign parent role and name of the delegated role.
    parent_role = 'targets'
    delegated_role = 'delegated_role_1'

    #  Create couple new RSA keys for delegation levels 1 and 2.
    new_keyid_1 = self.generate_rsakey()
    new_keyid_2 = self.generate_rsakey()

    #  Create temp directory for config file.
    config_dir = self.make_temp_directory()

    #  Build a config file.
    config_filepath = signerlib.build_config_file(config_dir, 365,
                                                  self.semi_roledict)

    #  Patch signercli._get_metadata_directory().
    self.mock_get_metadata_directory(directory=meta_dir)

    #  Patch signercli._get_password().  Get passwords for parent's keyids.
    self.get_passwords()

    #  Create keystore directory.
    keystore_dir = self.create_temp_keystore_directory()

    #  Mock method for signercli._prompt() to generate targets.txt file.
    self.make_metadata_mock_prompts(targ_dir=targets_dir,
                                    conf_path=config_filepath)

    #  List of keyids to be returned by _get_keyids()
    signing_keyids = [new_keyid_1]

    #  Load keystore.
    load_keystore = keystore.load_keystore_from_keyfiles

    #  Build targets metadata file (targets.txt).
    try:
      signercli.make_targets_metadata(keystore_dir)
    except Exception, e:
      self.fail(str(e))

    #  Clear kestore's dictionaries.
    keystore.clear_keystore()


    #  Mock method for signercli._prompt().
    def _mock_prompt(msg, junk):
      if msg.startswith('\nNOTE: The directory entered'):
        return delegated_targets_dir
      elif msg.startswith('\nChoose and enter the parent'):
        return parent_role
      elif msg.endswith('\nEnter the delegated role\'s name: '):
        return delegated_role
      else:
        error_msg = ('Prompt: '+'\''+msg+'\''+
                     ' did not match any predefined mock prompts.')
        self.fail(error_msg)


    #  Mock method for signercli._get_password().
    def _mock_get_password(msg):
      for keyid in self.rsa_keyids:
        if msg.endswith('('+keyid+'): '):
          return self.rsa_passwords[keyid]


    #  Method to patch signercli._get_keyids()
    def _mock_get_keyids(junk):
      if signing_keyids:
        for keyid in signing_keyids:
          password = self.rsa_passwords[keyid]
          #  Load the keyfile.
          load_keystore(keystore_dir, [keyid], [password])
      return signing_keyids


    #  Patch signercli._prompt().
    signercli._prompt = _mock_prompt

    #  Patch signercli._get_password().
    signercli._get_password = _mock_get_password

    #  Patch signercli._get_keyids().
    signercli._get_keyids = _mock_get_keyids



    # TESTS
    #  Test: invalid parent role.
    #  Assign a non-existing parent role.
    parent_role = self.random_string()
    self.assertRaises(tuf.RepositoryError, signercli.make_delegation,
                      keystore_dir)

    #  Restore parent role.
    parent_role = 'targets'


    #  Test: invalid password(s) for parent's keyids.
    keystore.clear_keystore()
    parent_keyids = self.semi_roledict[parent_role]['keyids']
    for keyid in parent_keyids:
      saved_pw = self.rsa_passwords[keyid]
      self.rsa_passwords[keyid] = self.random_string()
      self.assertRaises(tuf.RepositoryError, signercli.make_delegation,
                        keystore_dir)
      self.rsa_passwords[keyid] = saved_pw


    #  Test: delegated_keyids > 1 or (== 0).
    keystore.clear_keystore()

    #  Load keyids ( > 1).
    #  'signing_keyids' already contains 'new_keyid', add more.
    for keyid in self.semi_roledict['release']['keyids']:
      signing_keyids.append(keyid)
    self.assertRaises(tuf.RepositoryError, signercli.make_delegation,
                      keystore_dir)
    keystore.clear_keystore()

    #  Load 0 keyids (== 0).
    signing_keyids = []
    self.assertRaises(tuf.RepositoryError, signercli.make_delegation,
                      keystore_dir)
    keystore.clear_keystore()

    #  Restore signing_keyids (== 1).
    signing_keyids = [new_keyid_1]


    #  Test: normal case 1.
    #  Testing first level delegation.
    try:
      signercli.make_delegation(keystore_dir)
    except Exception, e:
      self.fail(str(e))

    #  Verify delegated metadata file exists.
    delegated_meta_file = os.path.join(meta_dir, parent_role,
                                       delegated_role+'.txt')
    self.assertTrue(os.path.exists(delegated_meta_file))


    #  Test: normal case 2.
    #  Testing second level delegation.
    keystore.clear_keystore()

    #  Make necessary adjustments for the test.
    signing_keyids = [new_keyid_2]
    delegated_targets_dir = os.path.join(delegated_targets_dir,
                                         'delegated_level2')
    parent_role = os.path.join(parent_role, delegated_role)
    delegated_role = 'delegated_role_2'

    try:
      signercli.make_delegation(keystore_dir)
    except Exception, e:
      self.fail(str(e))

    #  Verify delegated metadata file exists.
    delegated_meta_file = os.path.join(meta_dir, parent_role,
                                       delegated_role+'.txt')
    self.assertTrue(os.path.exists(delegated_meta_file))





# Run unit tests.
loader = unittest_toolbox.unittest.TestLoader
suite = loader().loadTestsFromTestCase(TestSignercli)
unittest_toolbox.unittest.TextTestRunner(verbosity=2).run(suite)
