"""
<Program Name>
  test_signerlib.py

<Author>
  Konstantin Andrianov

<Started>
  September 6, 2012

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test_signerlib.py provides collection of methods that tries to test all the
  units (methods) of the module under test.

  This unittest module requires setting of rsa keys, keyids and such.
  There is a method in unittest_toolbox.Modified_TestCase class
  'bind_keys_to_roles()'.  This method  will set dictionaries
  'semi_roledict' and 'rsa_keystore'.

  'semi_roledict' corresponds to ROLEDICT_SCHEMA and it looks like this:
    {'rolename': {'keyids': ['34345df32093bd12...'], 'threshold': 1}, ...}

  'rsa_keystore' looks like this: {keyid : { -- RSAKEY_SCHEMA --}, ... }  or
    {keyid : {'keytype': 'rsa', 'keyid': keyid,
              'keyval': {'public': 'PUBLIC KEY',
                         'private  ': 'PRIVATE KEY'}}, ... }

  unittest_toolbox module was created to provide additional testing tools for
  tuf's modules.  For more info see unittest_toolbox.py.


<Methodology>
  Unittests must follow a specific structure i.e. independent methods should
  be tested prior to dependent methods. More accurately: least dependent methods
  are tested before most dependent methods.  There is no reason to rewrite or
  construct other methods that replicate already-tested methods solely for
  testing purposes.  This is possible because 'unittest.TestCase' class guarantees
  the order of unit tests.  So that, 'test_something_A' method would be tested
  before 'test_something_B'.  To ensure the structure a number will be placed
  after 'test' and before methods name like so 'test_1_check_directory'.  The
  number is sort of a measure of dependence, where 1 is less dependent than 2.

"""

import os
import tempfile
import filecmp
import shutil
import ConfigParser
import gzip

import tuf.util
import tuf.formats as formats
import tuf.repo.signerlib as signerlib
import tuf.tests.unittest_toolbox

# 'unittest_toolbox.Modified_TestCase' is too long, I'll set it to 'unit_tbox'.
unit_tbox = tuf.tests.unittest_toolbox.Modified_TestCase
test_loader = tuf.tests.unittest_toolbox.unittest.TestLoader

# Generate rsa keys and roles dictionary dictionaries.
unit_tbox.bind_keys_to_roles()


class TestSignerlib(unit_tbox):
  # Test methods.


  def test_1_get_metadata_filenames(self):

    # SETUP
    metadata_dir = self.make_temp_directory()
    empty_dir = ''

    def _get_metadata_filenames(test_metadata_dir):
      filenames = signerlib.get_metadata_filenames(test_metadata_dir)
      if test_metadata_dir is None:
        test_metadata_dir = '.'

      #  Check if a dictionary instance with 4 mappings is returned.
      self.assertTrue(isinstance(filenames, dict))
      self.assertFalse(not filenames, 'Empty dictionary returned.')
      self.assertEqual(len(filenames), 4)

      #  Check if all the keys in 'filenames' dictionary
      #  correspond to 'role_list' items i.e. all top level
      #  roles are include in the 'filenames' with their
      #  appropriate paths as values.
      for role in unit_tbox.role_list:
        value_at_role = os.path.join(test_metadata_dir, role+'.txt')
        self.assertTrue(role in filenames)
        self.assertEqual(filenames[role], value_at_role)

    # Run _get_metadata_filenames(arg) trying different arguments.
    self.assertRaises(tuf.FormatError, signerlib.get_metadata_filenames, 123)
    _get_metadata_filenames(metadata_dir)
    _get_metadata_filenames(empty_dir)





  def test_1_get_metadata_file_info(self):

    # SETUP
    temp_file_path = self.make_temp_data_file()
    rand_str = self.random_string()


    # TESTS
    #  Test: improper arguments that should raise exceptions.
    self.assertRaises(tuf.Error, signerlib.get_metadata_file_info, '')
    self.assertRaises(tuf.FormatError, signerlib.get_metadata_file_info,
                      123)
    self.assertRaises(tuf.FormatError, signerlib.get_metadata_file_info,
                      {rand_str: rand_str})
    self.assertRaises(tuf.FormatError, signerlib.get_metadata_file_info,
                      [rand_str, rand_str])

    #  Make sure the format return by 'get_metadata_file_info'
    #  matches tuf.formats.FILEINFO_SCHEMA.
    file_info = signerlib.get_metadata_file_info(temp_file_path)
    self.assertTrue(formats.FILEINFO_SCHEMA.matches(file_info))





  def test_1_generate_and_save_rsa_key(self):
    """
    generate_and_save_rsa_key() is independent from all the other methods in
    signerlib.  In order to test this method all we need is to create a temp
    directory and a sample password.
    """

    # SETUP
    keystore_dir = self.make_temp_directory()
    password = self.random_string()



    # TESTS
    #  Test: Run generate_and_save_rsa_key().
    rsakey = signerlib.generate_and_save_rsa_key(keystore_dir, password)
    self.assertTrue(formats.RSAKEY_SCHEMA.matches(rsakey))


    #  Test: Check if rsa key file was created.
    key_path = os.path.join(keystore_dir, rsakey['keyid']+'.key')
    self.assertTrue(os.path.exists(key_path))





  def test_1_read_config_file(self):
    """
    Short test of 'read_config_file' method.  Using a tuple
    that contains config dictionary and a config file containing
    the same dictionary, test if 'read_config_file' returns a
    dictionary corresponding to the supplied config dictionary when
    config file is passes.
    """

    # SETUP
    #  'base_config' is a tuple containing a config file path and
    #  a corresponding config dictionary.  Note, make sure appropriate
    #  suffix is set.  In our case it will be 'signerlib.CONFIG_FILENAME'.
    base_config = self.make_temp_config_file(suffix=signerlib.CONFIG_FILENAME)



    # TESTS
    #  Test: normal case.
    self.assertTrue(signerlib.read_config_file(base_config[0]),
                    base_config[1])


    #  Test: exceptions.
    self.assertRaises(tuf.FormatError, signerlib.read_config_file, 123)
    self.assertRaises((tuf.Error, tuf.FormatError), signerlib.read_config_file,
                      '')
    self.assertRaises((tuf.Error, tuf.FormatError), signerlib.read_config_file,
                      'junk/dir/'+self.random_string())
    self.assertRaises(tuf.FormatError, signerlib.read_config_file,
                      [self.random_string()])





  def test_1_generate_targets_metadata(self):

    # SETUP
    generate_targets_meta = signerlib.generate_targets_metadata

    #  Generate target files.
    #  'repo_dir' represents repository base.
    #  'target_files' represents a list of relative target paths.
    repo_dir, target_files = self.make_temp_directory_with_data_files()
    print
    print 'Pringting :'
    print target_files
    print



    # TESTS
    #  Test: Run the generate_targets_metadata().  Test its return value.
    #  Its return value should correspond to tuf.formats.SIGNABLE_SCHEMA
    try:
      target_signable_obj = generate_targets_meta(repo_dir, target_files)
    except Exception, e:
      raise

    #  Test: Validate input.
    self.assertTrue(formats.SIGNABLE_SCHEMA.matches(target_signable_obj))


    #  Test: various invalid parameters.
    self.assertRaises(tuf.FormatError, generate_targets_meta,
                      repo_dir, 1234)
    self.assertRaises(tuf.FormatError, generate_targets_meta,
                      repo_dir, self.random_string())
    self.assertRaises(tuf.FormatError, generate_targets_meta,
                      repo_dir, [self.random_string(), 1234])
    self.assertRaises(tuf.Error, generate_targets_meta,
                      self.random_path(), target_files)





  def test_1_check_directory(self):
    """
      Quick test to ensure that the method returns valid output.
    """

    # SETUP
    temp_dir, _junk = self.make_temp_directory_with_data_files()
    rand_str = self.random_string()



    # TESTS
    #  Test: normal case, check proper output.
    self.assertEqual(signerlib.check_directory(temp_dir), temp_dir)


    # Test exceptions.
    self.assertRaises(tuf.FormatError, signerlib.check_directory, 1234)
    self.assertRaises(tuf.FormatError, signerlib.check_directory, [rand_str])
    self.assertRaises(tuf.FormatError, signerlib.check_directory,
                      {rand_str: rand_str})
    self.assertRaises(tuf.Error, signerlib.check_directory, self.random_path())





  def test_1_write_metadata_file(self):

    # SETUP
    #   Create temp directory to be prevent any relative path discrepancies.
    meta_dir = self.make_temp_directory()

    #  Create a temp file to store 'metadata' info in.
    meta_file = self.make_temp_file(directory=meta_dir)

    #  Use valid input for json obj.
    signable_dict = {'signatures':[], 'signed':{'role':'info'}}



    # TESTS
    #  Test: normal case.
    try:
      signerlib.write_metadata_file(signable_dict, meta_file)
    except Exception, e:
      raise

    #  Extract the content of the temp file.
    stored_signable_dict = tuf.util.load_json_file(meta_file)

    #  Check if object stored in the file corresponds to SIGNABLE_SCHEMA.
    self.assertTrue(formats.SIGNABLE_SCHEMA.matches(stored_signable_dict))

    # Does original dictionary 'signable_dict' matches dictionary retrieved
    # from the file - 'stored_signable_dict'?
    self.assertEqual(signable_dict, stored_signable_dict)


    # Test: verify exceptions.
    self.assertRaises(tuf.FormatError, signerlib.write_metadata_file,'','')
    self.assertRaises(tuf.FormatError, signerlib.write_metadata_file,
                      [self.random_string()], meta_file)
    self.assertRaises(tuf.FormatError, signerlib.write_metadata_file,
                      signable_dict, [self.random_string()])
    self.assertRaises(tuf.Error, signerlib.write_metadata_file, signable_dict,
                      self.random_path())
    self.assertRaises(tuf.FormatError, signerlib.write_metadata_file,
                      {self.random_string(): self.random_string()},
                      self.random_path())



  def test_2_build_config_file(self):
    """
      This method tests build_config_file().
      Previously tested signerlib's read_config_file() is used here.
    """

    # SETUP
    #  Declare timeout.
    days = 365  # number of days

    #  Make a temp directory for config file.
    config_dir = self.make_temp_directory()

    #  For 'role_info' argument we going to use 'self.semi_roledict'
    #  dictionary.  There is more info in the beginning of this test
    #  module, also in the test.unittest_toolbox module.
    roledict_info = self.semi_roledict



    # TESTS
    #  Test: normal case.
    #  Run build_config_file().  The method is expected to return file
    #  path of the config file.  We'll compare it to 'roledict_info'.
    build_config = signerlib.build_config_file
    try:
      config_path = build_config(config_file_directory=config_dir,
                                 timeout=days, role_info=roledict_info)
    except Exception, e:
      raise

    #  Check if 'config_path' directory exists.
    self.assertTrue(os.path.exists(config_path))

    #  Using 'signerlib.read_config_file' method extract config dictionary
    #  that was stored.
    config_dict = signerlib.read_config_file(config_path)

    #  Remove 'expiration' key from the extracted config dictionary, since
    #  initial role dictionary does not have this field.
    del config_dict['expiration']

    #  Compare the initial dictionary 'roledict_info' with extracted
    #  dictionary 'config_dict'.  They have to match.
    self.assertTrue(config_dict, roledict_info)


    #  Test: exceptions on bogus arguments.
    self.assertRaises(tuf.Error, signerlib.build_config_file,
                      self.random_path(), 365, roledict_info)
    self.assertRaises(tuf.FormatError, signerlib.build_config_file,
                      config_dir, -1, roledict_info)
    self.assertRaises(tuf.FormatError, signerlib.build_config_file,
                      config_dir, 365, self.directory_dictionary)



  def test_3_generate_root_metadata(self):
    """
      test_3_build_root_metadata() is based on two other signerlib methods
      i.e. build_config_file() and read_config_file().  Hence, 3rd level.
    """

    # SETUP
    build_config = signerlib.build_config_file

    #  Create a temp directory to hold a config file.
    config_dir = self.make_temp_directory()

    #  Create config file using previously tested build_config_file().
    config_path = build_config(config_dir, 365, self.semi_roledict)

    #  Create a config file without a 'targets' role section.
    notargets_conf_dir = self.make_temp_directory()
    saved_targets_role = self.semi_roledict['targets']
    del self.semi_roledict['targets']
    notargets_conf_path = build_config(notargets_conf_dir, 365,
                                       self.semi_roledict)

    #  Restore semi_roledict to initial state.
    self.semi_roledict['targets'] = saved_targets_role



    # TESTS
    #  Test: What if keystore is not set up?
    self.assertRaises(tuf.UnknownKeyError, signerlib.generate_root_metadata,
                      config_path)


    #  Patch keystore's get_key method.  No harm is done here since correct
    #  arguments are passed and keystore methods are tested separately.
    signerlib.tuf.repo.keystore.get_key = self.get_keystore_key

    #  Test: normal case.  Pass a correct config path.
    try:
      root_meta = signerlib.generate_root_metadata(config_path)
    except Exception, e:
      raise

    #  Check if the returned dictionary corresponds to SIGNABLE_SCHEMA.
    self.assertTrue(formats.SIGNABLE_SCHEMA.matches(root_meta))


    #  Test: bogus arguments.
    self.assertRaises(tuf.Error, signerlib.generate_root_metadata,
                      notargets_conf_path)
    self.assertRaises(tuf.Error, signerlib.generate_root_metadata, '')
    self.assertRaises(tuf.Error, signerlib.generate_root_metadata,
                      self.random_string())
    self.assertRaises(tuf.Error, signerlib.generate_root_metadata,
                      {self.random_string(): self.random_string()})





  def test_4_sign_metadata(self):
    """
    test_4_sign_metadata() will require us to create metadata using one of
    the generate_role_metadata() and use monkey patched keystore's get_key().
    """

    for role in ['root', 'targets']:

      # SETUP.
      role_info = self._get_role_info(role)
      filename = role+'.txt'

      #  Test: normal case.
      try:
        signable = signerlib.sign_metadata(role_info[0], role_info[1],
                                           filename)
      except Exception, e:
        raise

      #  Check if signable is returned.
      self.assertTrue(formats.SIGNABLE_SCHEMA.matches(signable))


      #  Test: various bogus parameters.
      self.assertRaises(tuf.FormatError, signerlib.sign_metadata,
                        self.random_string(), role_info[1], filename)
      self.assertRaises(tuf.FormatError, signerlib.sign_metadata,
                        role_info[0], 12345, filename)


      #  Test: Verifying 'keytype', once is sufficient.
      if role == 'root':

        #  Alter keytype field of the rsa key.  Restore it after.
        for keyid in role_info[1]:
          key = self.get_keystore_key(keyid)
          key['keytype'] = 'unknown_type'
        self.assertRaises(tuf.Error, signerlib.sign_metadata, role_info[0],
            role_info[1], filename)

        #  Restoring the initial state of rsa_keystore.
        for keyid in role_info[1]:
          key = self.get_keystore_key(keyid)
          key['keytype'] = 'rsa'





  def test_5_build_root_file(self):
    """
    test_5_build_root_file() relies on previously tested signerlib's
    generate_root_metadata(), sign_metadata() and write_metadata_file().
    build_root_file() basically joins these methods together to create
    root.txt.

    Test Outline: Get signed metadata and other info of a root role.
    'root_meta' is a tuple - see _get_role_meta() and _get_signed_role_info().
    Run build_root_file() with created parameters 'config_path', 'root_keyids'
    and 'meta_dir'.  Verify existence of the created directory.  Extract
    content of the file and verify that it matches original 'signed_root_meta'
    dictionary.  Test various bogus parameters.
    """

    # SETUP
    signed_root_meta, root_info = self._get_signed_role_info('root')
    root_keyids = root_info[1]
    config_path = root_info[3]
    meta_dir = root_info[2]  # Reuse config's directory.
    root_meta_path = os.path.join(meta_dir, 'root.txt')



    # TESTS
    #  Test: normal case.
    try:
      signerlib.build_root_file(config_path, root_keyids, meta_dir)
    except Exception, e:
      raise

    #  Check existence of the file and validity of it's content.
    self.assertTrue(os.path.exists(root_meta_path))
    file_content = tuf.util.load_json_file(root_meta_path)
    self.assertEqual(signed_root_meta, file_content)


    #  Test: variouse exeptions.
    self.assertRaises(tuf.Error, signerlib.build_root_file,
        self.random_path(), root_keyids, meta_dir)
    self.assertRaises(tuf.Error, signerlib.build_root_file,
        config_path, root_keyids, self.random_path())
    self.assertRaises(tuf.FormatError, signerlib.build_root_file,
        config_path, self.random_string(), meta_dir)





  def test_5_builds_targets_file(self):
    """
    test_5_build_targets_file() relies on previously tested signerlib's
    generate_targets_metadata(), sign_metadata() and write_metadata_file().
    build_targets_file() basically joins these methods together to create
    targets.txt.
    """

    # SETUP
    signed_targets_meta, targets_info = self._get_signed_role_info('targets')

    #  'targets_info' is a tuple that includes targets meta, repository dir,
    #  list of target files.
    targets_keyids = targets_info[1]
    repo_dir = targets_info[2]
    meta_dir = os.path.join(repo_dir, 'metadata')
    os.mkdir(meta_dir)
    targets_file_path = os.path.join(meta_dir, 'targets.txt')
    targets_dir = os.path.join(repo_dir, 'targets')



    # TESTS
    #  Test: normal case.
    try:
      signerlib.build_targets_file(targets_dir, targets_keyids, meta_dir)
    except Exception, e:
      raise

    #  Check existence of the file and validity of it's content.
    self.assertTrue(os.path.exists(targets_file_path))
    file_content = tuf.util.load_json_file(targets_file_path)
    self.assertEqual(signed_targets_meta, file_content)


    #  Test: variouse exeptions.
    self.assertRaises(tuf.Error, signerlib.build_targets_file,
        self.random_path(), targets_keyids, meta_dir)
    self.assertRaises(tuf.FormatError, signerlib.build_root_file,
        targets_dir, self.random_string(), meta_dir)
    self.assertRaises((tuf.FormatError, tuf.Error), signerlib.build_root_file,
        targets_dir, targets_keyids, self.random_path())





  def test_6_generate_release_metadata(self):
    """
    test_6_generate_release_metadata() uses previously tested
    singnerlib's build_root_file(), build_target_file()
    and get_metadata_file_info.  In order to use generate_release_metadata()
    we need to have root.txt and targets.txt in the metadata directory,
    plus we need to have targets directory (with target files/directories).
    """

    # SETUP
    #  Create root.txt and targets.txt as described above.
    meta_dir = self._create_root_and_targets_meta_files()



    # TESTS
    #  Test: Run generate_release_metadata().
    try:
      release_meta = signerlib.generate_release_metadata(meta_dir)
    except Exception, e:
      raise

    #  Verify that created metadata dictionary corresponds to
    #  SIGNABLE_SCHEMA and its 'signed' value to RELEASE_SCHEMA.
    self.assertTrue(formats.SIGNABLE_SCHEMA.matches(release_meta))
    self.assertTrue(formats.RELEASE_SCHEMA.matches(release_meta['signed']))


    #  Test: exceptions.
    self.assertRaises(tuf.Error, signerlib.generate_release_metadata,
                      self.random_path())
    self.assertRaises(tuf.FormatError, signerlib.generate_release_metadata,
                      ['junk'])





  def test_7_build_release_file(self):
    """
    test_7_build_release_file() uses previously tested
    generate_release_metadata().
    """

    # SETUP
    #  Create root.txt and targets.txt as described above.  Also, get signed
    #  release metadata to compare it with the content of the file
    signed_release_meta, release_info = self._get_signed_role_info('release')
    meta_dir = release_info[2]
    release_keyids = release_info[1]
    release_filepath = os.path.join(meta_dir, 'release.txt')



    # TESTS
    #  Test: normal case.
    try:
      signerlib.build_release_file(release_keyids, meta_dir)
    except Exception, e:
      raise

    # Check if 'release.txt' file was created in metadata directory.
    self.assertTrue(os.path.exists(release_filepath))
    file_content = tuf.util.load_json_file(release_filepath)
    self.assertEqual(file_content, signed_release_meta)


    #  Test: exceptions.
    self.assertRaises(tuf.Error, signerlib.build_release_file, release_keyids,
                      self.random_path())
    self.assertRaises(tuf.FormatError, signerlib.build_release_file,
                      self.random_string(), meta_dir)





  def test_8_generate_timestamp_metadata(self):
    """
    test_8_generate_timestamp_metadata() uses previously tested
    build_release_file()
    """

    # SETUP
    generate_timestamp_meta = signerlib.generate_timestamp_metadata


    #  Create release metadata and create 'release.txt' file.
    junk, release_keyids, meta_dir = self._get_role_info('release')
    signerlib.build_release_file(release_keyids, meta_dir)
    release_filepath = os.path.join(meta_dir, 'release.txt')

    #  To test compression we need to create compressed 'release.txt'.
    #  The 'release.txt' should exist at this point, compress it.
    release_file = open(release_filepath, 'rb')
    gzipped_release = open(release_filepath+'.gz', 'wb')
    gzipped_release.writelines(release_file)
    gzipped_release.close()
    release_file.close()



    # TESTS
    #  Test: normal case.
    try:
      timestamp_meta = generate_timestamp_meta(release_filepath)
    except Exception, e:
      raise

    #  Verify metadata formats.
    self.assertTrue(formats.SIGNABLE_SCHEMA.matches(timestamp_meta))
    self.assertTrue(formats.TIMESTAMP_SCHEMA.matches(timestamp_meta['signed']))


    #  Test: normal case (with compression).
    try:
      timestamp_meta = generate_timestamp_meta(release_filepath+'.gz')
    except Exception, e:
      raise

    #  Verify metadata formats.
    self.assertTrue(formats.SIGNABLE_SCHEMA.matches(timestamp_meta))
    self.assertTrue(formats.TIMESTAMP_SCHEMA.matches(timestamp_meta['signed']))


    #  Test: invalid path.
    self.assertRaises(tuf.Error, generate_timestamp_meta, self.random_path())





  def test_9_build_timestamp_metadata(self):
    """
    test_9_build_timestamp_file() uses previously tested
    generate_timestamp_metadata().
    """

    # SETUP
    #  Create all necessary files and metadata i.e. signed timestamp
    #  metadata, timestamp keyids, 'release.txt', 'root.txt', 'targets.txt',
    #  target files, etc.
    signed_timestamp_meta, timestamp_info = \
        self._get_signed_role_info('timestamp')

    timestamp_keyids = timestamp_info[1]
    meta_dir = timestamp_info[2]
    timestamp_filepath = os.path.join(meta_dir, 'timestamp.txt')



    # TESTS
    #  Test: normal case.
    try:
      signerlib.build_timestamp_file(timestamp_keyids, meta_dir)
    except Exception, e:
      raise

    # Check if 'timestamp.txt' file was created in metadata directory.
    self.assertTrue(os.path.exists(timestamp_filepath))
    file_content = tuf.util.load_json_file(timestamp_filepath)
    self.assertEqual(file_content, signed_timestamp_meta)


    #  Test: try bogus parameters.
    self.assertRaises(tuf.Error, signerlib.build_timestamp_file,
                      timestamp_keyids, self.random_path())
    self.assertRaises(tuf.FormatError, signerlib.build_timestamp_file,
                      self.random_string(), meta_dir)





  def test_9_get_target_keyids(self):
    '''
    # SETUP
    #  Create metadata directory and targets metadata file.
    meta_dir = self._create_root_and_targets_meta_files()

    signed_targets_meta, targets_info = self._get_signed_role_info('targets')

    #  'targets_info' is a tuple that includes targets meta, repository dir,
    #  list of target files.
    targets_keyids = targets_info[1]
    repo_dir = targets_info[2]
    meta_dir = os.path.join(repo_dir, 'metadata')
    os.mkdir(meta_dir)
    targets_file_path = os.path.join(meta_dir, 'targets.txt')
    targets_dir = os.path.join(repo_dir, 'targets')



    # TESTS
    #  Test: normal case.
    try:
      signerlib.build_targets_file(targets_dir, targets_keyids, meta_dir)
    except Exception, e:
      raise

    #  Check existence of the file and validity of it's content.
    self.assertTrue(os.path.exists(targets_file_path))
    file_content = tuf.util.load_json_file(targets_file_path)
    self.assertEqual(signed_targets_meta, file_content)
    #  Generate some delegation metadata file.
    '''
    pass






  # HELPER METHODS
  # Call these non-test methods ONLY in methods that begin with 'test'.
  def _create_root_and_targets_meta_files(self, repo_dir=None):
    """
    This method generates temp root.txt and target.txt, it uses following
    previously tested signerlib's methods:
      build_root_file()
      build_targets_file()
    """

    if not repo_dir:

      # Create repository directory.
      repo_dir = self.make_temp_directory()


    # Create metadata directory.
    meta_dir = os.path.join(repo_dir, 'metadata')
    os.mkdir(meta_dir)

    # Create root.txt.
    junk, root_keyids, repo_dir, config_path = \
        self._get_role_info('root', directory=repo_dir)
    signerlib.build_root_file(config_path, root_keyids, meta_dir)
    self.assertTrue(os.path.exists(os.path.join(meta_dir, 'root.txt')))

    # Create targets.txt.
    junk, targets_keyids, repo_dir, target_files = \
        self._get_role_info('targets', directory=repo_dir)
    path_to_targets = os.path.join(repo_dir, 'targets')
    signerlib.build_targets_file(path_to_targets, targets_keyids, meta_dir)
    self.assertTrue(os.path.exists(os.path.join(meta_dir, 'root.txt')))

    return meta_dir





  def _get_role_info(self, role, directory=None):
    """
    This method generates role's metadata dictionary, it uses previously
    tested signerlib's methods.  Note that at everything maintains the order.
    Nothing that has not been tested previously is used in any of the
    following conditions.

    <Arguments>
      directory:
        Directory of a config file.

    <Returns>
      Tuple (role's metadata(not signed), role's keyids, directory, optional)

    """

    if not directory:
      # Create a temp directory to hold a config file.
      directory = self.make_temp_directory()

    # Get role's keyids.
    role_keyids = self.semi_roledict[role]['keyids']



    if role == 'root':
      #  Create config file using previously tested build_config_file().
      config_path = signerlib.build_config_file(directory, 365,
                                                self.semi_roledict)

      #  Patch keystore's get_key method.
      signerlib.tuf.repo.keystore.get_key = self.get_keystore_key

      #  Create root metadata.
      root_meta = signerlib.generate_root_metadata(config_path)
      return root_meta, role_keyids, directory, config_path


    elif role == 'targets':
      # Generate target files.
      # 'repo_dir' represents repository base.
      # 'target_files' represents a list of relative target paths.
      repo_dir, target_files = \
          self.make_temp_directory_with_data_files(directory=directory)

      # Run the 'signerlib.generate_targets_metadata'.  Test its return value.
      # Its return value should correspond to tuf.formats.SIGNABLE_SCHEMA
      targets_meta = signerlib.generate_targets_metadata(repo_dir,
                                                         target_files)
      return targets_meta, role_keyids, repo_dir, target_files


    elif role == 'release':
      # Generate 'root.txt' and 'targets.txt' with targets directory in
      # the repository containing files and directories.
      meta_dir = self._create_root_and_targets_meta_files()
      release_meta = signerlib.generate_release_metadata(meta_dir)
      return release_meta, role_keyids, meta_dir


    elif role == 'timestamp':
      # Generate 'release.txt' which includes creation of 'root.txt',
      # 'targets.txt' and target files.
      junk, release_keyids, meta_dir = self._get_role_info('release')
      signerlib.build_release_file(release_keyids, meta_dir)
      release_filepath = os.path.join(meta_dir, 'release.txt')

      # Generate timestamp metadata.
      timestamp_meta = signerlib.generate_timestamp_metadata(release_filepath)
      return timestamp_meta, role_keyids, meta_dir


    else:
      print '\nUnrecognized top-level role.'





  def _get_signed_role_info(self, role, directory=None):
    role_info = self._get_role_info(role, directory=directory)
    filename = repr(role+'.txt')

    # Try sign_metadata(), see if signable is returned.
    signed_meta = signerlib.sign_metadata(role_info[0], role_info[1],
                                          filename)
    return signed_meta, role_info





# RUN UNIT TESTS.
print
suite = test_loader().loadTestsFromTestCase(TestSignerlib)
tuf.tests.unittest_toolbox.unittest.TextTestRunner(verbosity=2).run(suite)
