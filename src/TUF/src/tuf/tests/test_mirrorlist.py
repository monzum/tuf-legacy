"""
<Program Name>
  test_mirrorlist.py

<Author>
  Konstantin Andrianov

<Started>
  October 27, 2012

<Purpose>
  Test mirrorlist.py module.

"""

import os
import shutil
import tempfile
import quickstart
import tuf.formats
import tuf.mirrorlist
import tuf.tests.unittest_toolbox

tuf.tests.unittest_toolbox.Modified_TestCase.bind_keys_to_roles()



class TestMirrorlist(tuf.tests.unittest_toolbox.Modified_TestCase):

  def test_1_add_mirror(self):
    
    def _mock_prompt(msg, junk=str):
      if msg.startswith('Enter mirror\'s name'):
        return 'mirror1'
      elif msg.startswith('Enter mirror\'s URL'):
        return 'http://localhost:8001'
      elif msg.startswith('Enter directory where metadata'):
        return 'metadata'
      elif msg.startswith('Enter directory where target'):
        return 'targets'
      elif msg.startswith('Enter number of confined paths'):
        return '0'

    # Patching tuf.mirrorlist.prompt method
    tuf.mirrorlist._prompt = _mock_prompt

    tuf.mirrorlist.add_mirror()

    check_format = tuf.formats.MIRROR_SCHEMA.matches
    self.assertTrue(check_format(tuf.mirrorlist.mirrorlist_dict['mirror1']))





  def test_remove(self):

    tuf.mirrorlist.mirrorlist_dict = {}

    def _mock_prompt(msg, junk=str):
      if msg.startswith('Enter mirror\'s name'):
        return 'mirror2'
      elif msg.startswith('Enter mirror\'s URL:'):
        return 'http://localhost:8002'
      elif msg.startswith('Enter directory where metadata'):
        return 'metadata'
      elif msg.startswith('Enter directory where target'):
        return 'targets'
      elif msg.startswith('Enter number of confined paths'):
        return '0'
      elif msg.startswith('Enter mirror\'s URL to remove'):
        return 'http://localhost:8002'
      elif msg.startswith('Do you want to add a mirror'):
        return 'n'

    tuf.mirrorlist._prompt = _mock_prompt

    tuf.mirrorlist.add_mirror()
    self.assertEqual(len(tuf.mirrorlist.mirrorlist_dict), 1)

    check_format = tuf.formats.MIRROR_SCHEMA.matches
    self.assertTrue(check_format(tuf.mirrorlist.mirrorlist_dict['mirror2']))

    tuf.mirrorlist.remove_mirror()
    self.assertEqual(len(tuf.mirrorlist.mirrorlist_dict), 0)

    tuf.mirrorlist.mirrorlist_dict = self.mirrors 

 


  def test_2_generate_mirrorlist_metadata(self):
    def _mock_prompt(msg, junk=str):
      return 'n'
    tuf.mirrorlist._prompt = _mock_prompt
    mirrorlist_meta = tuf.mirrorlist.generate_mirrorlist_metadata(self.mirrors)
    check_format = tuf.formats.MIRRORLIST_SCHEMA.matches
    self.assertTrue(check_format(mirrorlist_meta['signed']))





  def test_3_build_mirrorlist_file(self):
    self.create_temp_keystore_directory(keystore_dicts=True)
    meta_dir = self.make_temp_directory()
    keyids = self.semi_roledict['mirrorlist']['keyids']
    tuf.mirrorlist.build_mirrorlist_file(self.mirrors, keyids, meta_dir)
    os.path.exists(os.path.join(meta_dir, 'mirrorlist.txt'))




  def mock_download_file(self, file_path):
    """
    <Purpose>
      Pathch 'tuf.download.download_url_to_fileobject' method.
      
    <Arguments>
      file_path:
        Path to a file that will be returned as a tuf.util.TempFile
        fileobject.

    """

    def _mock_download_url_to_tempfileobj(url):
      file_obj = open(file_path, 'rb')
      temp_fileobj = tuf.util.TempFile()
      temp_fileobj.write(file_obj.read())
      return temp_fileobj

    # Patch tuf.download.download_url_to_tempfileobj().
    tuf.download.download_url_to_tempfileobj = \
    _mock_download_url_to_tempfileobj



  def setup_repositories(self):
    proj_files = self.make_temp_directory_with_data_files()
    proj_dir = os.path.join(proj_files[0], 'targets')

    input_dict = {'expiration':'12/12/2013',
                  'root':{'threshold':1, 'password':'pass'},
                  'targets':{'threshold':1, 'password':'pass'},
                  'release':{'threshold':1, 'password':'pass'},
                  'timestamp':{'threshold':1, 'password':'pass'},
                  'mirrorlist':{'threshold':1, 'password':'pass'}}

    def _mock_prompt(message, junk=str, input_parameters=input_dict):
      if message.startswith('\nWhen would you like your '+
          'certificates to expire?'):
        return input_parameters['expiration']
      for role in self.role_list+['mirrorlist']:  # role_list=['root', 'targets', ...]
        if message.startswith('\nEnter the desired threshold '+
            'for the role '+repr(role)):
          return input_parameters[role]['threshold']
        elif message.startswith('Enter the password for '+repr(role)):
          for threshold in range(input_parameters[role]['threshold']):
            if message.endswith(repr(role)+' ('+str(threshold+1)+'): '):
              return input_parameters[role]['password']
      print 'Cannot recognize message: '+message

    # Monkey patching quickstart's _prompt() and _get_password.
    quickstart._prompt = _mock_prompt
    quickstart._get_password = _mock_prompt

    quickstart.build_repository(proj_dir)





  def test_4_update_mirrorlist(self):
    # SETUP
    self.setup_repositories()

    cwd_dir = os.getcwd()
    
    meta_dir = os.path.join(cwd_dir, 'client', 'metadata')
    current_dir = os.path.join(meta_dir, 'current') 
    previous_dir = os.path.join(meta_dir, 'previous') 
   
    new_mirrorlist_filepath = os.path.join(current_dir, 'mirrorlist.txt') 

    # Patch tuf.download.download_url_to_tempfileobj function.
    self.mock_download_file(new_mirrorlist_filepath)

    tuf.mirrorlist.update_mirrorlist('junk', meta_dir)
    
    shutil.rmtree(os.path.join(cwd_dir, 'client'))
    shutil.rmtree(os.path.join(cwd_dir, 'repository'))
    shutil.rmtree(os.path.join(cwd_dir, 'keystore'))
    





  def test_load_mirrorlist_from_file(self):
    self.setup_repositories()
    cwd_dir = os.getcwd()
    meta_dir = os.path.join(cwd_dir, 'client', 'metadata')
    current_dir = os.path.join(meta_dir, 'current')
    mirrorlist_filepath = os.path.join(current_dir, 'mirrorlist.txt') 
    mirrors_dict = tuf.mirrorlist.load_mirrorlist_from_file(mirrorlist_filepath)
    #self.assertTrue(isinstance(mirrors_dict, dict))
    print mirrors_dict   

    shutil.rmtree(os.path.join(cwd_dir, 'client'))
    shutil.rmtree(os.path.join(cwd_dir, 'repository'))
    shutil.rmtree(os.path.join(cwd_dir, 'keystore'))










test_loader = tuf.tests.unittest_toolbox.unittest.TestLoader
suite = test_loader().loadTestsFromTestCase(TestMirrorlist)
tuf.tests.unittest_toolbox.unittest.TextTestRunner(verbosity=2).run(suite)

