"""
<Program Name>
  test_updater.py

<Author>
  Konstantin Andrianov

<Started>
  September 20, 2012

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  test_updater.py provides collection of methods that tries to test all the
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
import tempfile

import tuf.util
import tuf.client.updater as updater
#  Helper module unittest_toolbos.py
import tuf.tests.test_updater_setup as setup


#  References to tuf.unittest_toolbox modules and
#  tuf.unittest_toolbox.Modified_TestCase object.
unittest_toolbox = setup.unittest_toolbox  # unittest_toolbox
TestCase_Tools = setup.TestCase_Tools  # unittest_toolbox.Modified_TestCase

#  References to roledb and keydb dictionaries.
roledb_dict = tuf.roledb.roledb_dict
keydb_dict = tuf.keydb.keydb_dict

class TestUpdater_init_(unittest_toolbox.Modified_TestCase):

  def test__init__exceptions(self):
    
    # SETUP
    #  Create an empty repository structure for client.
    repo_dir = self.make_temp_directory()

    #  Patch config.
    tuf.conf.repository_directory = repo_dir



    # TESTS
    #  Test: empty repository. 
    self.assertRaises(tuf.RepositoryError, updater.Repository, 'Repo_Name',
                      self.mirrors) 


    #  Test: empty repository with {repository_dir}/metadata directory.
    meta_dir = os.path.join(repo_dir, 'metadata')
    os.mkdir(meta_dir)
    self.assertRaises(tuf.RepositoryError, updater.Repository, 'Repo_Name',
                      self.mirrors) 


    #  Test: empty repostiry with {repository_dir}/metadata/current directory.
    current_dir = os.path.join(meta_dir, 'current')
    os.mkdir(current_dir)
    self.assertRaises(tuf.RepositoryError, updater.Repository, 'Repo_Name',
                      self.mirrors)





class TestUpdater(unittest_toolbox.Modified_TestCase):
  
  #  Create repositories.  'repositories' is a tuple that looks like this:
  #  (repository_dir, client_repository_dir, server_repository_dir), see 
  #  updater_setup module.
  repositories = setup.create_repositories()



  def setUp(self):

    #  We are inhereting from custom class.
    unittest_toolbox.Modified_TestCase.setUp(self)

    #  Patching 'tuf.conf.repository_directory' with the one we set up.
    tuf.conf.repository_directory = self.repositories['client_repository']

    #  Populate client's 'metadata/current' directory. 
    setup.client_repository_include_all_role_files(self.repositories['main_repository'])

    #  Creating Repository instance.
    self.Repository = updater.Repository('Client_Repository', self.mirrors)

    print
    print len(roledb_dict)
    for item in roledb_dict.items():
      print item





  def tearDown(self):
    #  We are inhereting from custom class.
    unittest_toolbox.Modified_TestCase.tearDown(self)

    #  Clear roledb and keydb dictionaries.
    print '\n\nHERE\n\n'
    roledb_dict.clear()
    keydb_dict.clear()
    print
    print len(roledb_dict)
    for item in roledb_dict.items():
      print item
    print '\nDONE\n'





  def test_1__load_metadata_from_file(self):

    # SETUP
    meta_set = 'current'
    
    #  Lets get root metadata object.
    root_filepath = os.path.join(self.repositories['client_repository'],
                                 'metadata', meta_set, 'root.txt')
  
    #  Extract root metadata.
    root_meta = tuf.util.load_json_file(root_filepath)



    # TESTS
    #  Test: normal case.
    for role in self.role_list:
      try:
        self.Repository._load_metadata_from_file(meta_set, role)
      except Exception:
        raise

    #  Veryfy that the correct number of metadata objects has been loaded. 
    self.assertEqual(len(self.Repository.metadata[meta_set]), 4)

    #  Verify that the content of root metadata is valid.
    self.assertEqual(self.Repository.metadata[meta_set]['root'],
                     root_meta['signed'])






  def test_1__rebuild_key_and_role_db(self):
    
    # SETUP
    root_meta = self.Repository.metadata['current']['root']
   
    # TESTS
    #  Test: normal case.
    try:
      self.Repository._rebuild_key_and_role_db()
    except Exception:
      raise
    
    #  Verify tuf.rolebd.roledb_dict and tuf.keydb.keydb_dict dictionaries
    #  are populated.
    self.assertEqual(roledb_dict, self.top_level_role_info)
    self.assertEqual(len(keydb_dict), 4)

    #  Verify that keydb dictionary was updated.
    for role in self.role_list:
      keyids = self.top_level_role_info[role]['keyids']
      for keyid in keyids:
        self.assertTrue(keydb_dict[keyid])

    





  def test_2__import_delegations(self):
    # In order to test '_import_delegations' the parent of the delegation
    # has to be in Repository.metadata['current'].

    # TESTS
    #  Test: pass a role without delegations.
    try:
      self.Repository._import_delegations('root')
    except Exception:
      raise

    #  Verify that there was no change in roledb and keydb dictionaries
    #  by checking the number of elements in the dictionaries.
    self.assertEqual(len(roledb_dict), 5)
    self.assertEqual(len(keydb_dict), 5)

 
    #  Test: normal case, first level delegation.
    try:
      self.Repository._import_delegations('targets')
    except Exception:
      raise

    self.assertEqual(len(roledb_dict), 5)
    self.assertEqual(len(keydb_dict), 5)

    #  Verify that roledb dictionary was updated.
    self.assertTrue(tuf.roledb.roledb_dict['targets/delegated_role1'])

    #  Verify that keydb dictionary was updated.
    keyids = self.semi_roledict['targets/delegated_role1']['keyids']
    for keyid in keyids:
      self.assertTrue(keydb_dict[keyid])





  def test_3__ensure_all_targets(self):
    
    # SETUP
    #print
    #print self.Repository    

    """
    # TESTS
    #  Test: normal case.
    try:
      self.Repository._ensure_all_targets()
    except Exception:
      raise
    """




  def test_3__updata_metadata(self):
    pass
    # SETUP
    #  Patch download_file: return file object using utils.
     
    



    # TESTS








# Run all unit tests from test cases.

loader = unittest_toolbox.unittest.TestLoader()
suite = unittest_toolbox.unittest.TestSuite()

class1_tests = loader.loadTestsFromTestCase(TestUpdater_init_)
class2_tests = loader.loadTestsFromTestCase(TestUpdater)
 
suite.addTest(class1_tests)
suite.addTest(class2_tests)

unittest_toolbox.unittest.TextTestRunner(verbosity=2).run(suite)


#  Removing repositories.
setup.remove_all_repositories(TestUpdater.repositories['main_repository'])
print os.path.exists(TestUpdater.repositories['main_repository'])
