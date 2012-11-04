import tuf.tests.unittest_toolbox as ut
import os

ut.Modified_TestCase.bind_keys_to_roles()

class scrap_test(ut.Modified_TestCase):
  test_dir_structure = {'level1':{'level2':['file_data', 'file_data']},
      'another_level1':['file_data', {'level2':'file_data'}],
      'yet_another_level1':'file_data'}

  def _test_1(self):

    self.directory_dictionary = self.test_dir_structure
    main_dir =\
    self.make_temp_directory_with_data_files()
    print main_dir
    for dirname, dirnames, filenames in os.walk(main_dir[0]):
      for subdirname in dirnames:
        print os.path.join(dirname, subdirname)
      for filename in filenames:
        print os.path.join(dirname, filename)

  def test_2(self):
    keystore = self.create_temp_keystore_directory()
    for dirname, dirnames, filenames in os.walk(keystore):
      for subdirname in dirnames:
        print os.path.join(dirname, subdirname)
      for filename in filenames:
        print os.path.join(dirname, filename)


  def test_make_temp_dir_with_files(self):
    proj_dir = self.make_temp_directory_with_data_files()
    print
    print os.listdir(os.path.join(proj_dir[0], 'targets'))
    print



# RUN THE TESTS.
print
suite = ut.unittest.TestLoader().loadTestsFromTestCase(scrap_test)
ut.unittest.TextTestRunner(verbosity=2).run(suite)
