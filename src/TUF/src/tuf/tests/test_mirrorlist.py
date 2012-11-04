import tuf.formats
import tuf.mirrorlist
import tuf.tests.unittest_toolbox

class TestMirrorlist(tuf.tests.unittest_toolbox.Modified_TestCase):

  def test_add_mirror(self):
    
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
        return 'http://localhost:8001'
      elif msg.startswith('Do you want to add a mirror'):
        return 'n'

    tuf.mirrorlist._prompt = _mock_prompt

    tuf.mirrorlist.add_mirror()
    self.assertEqual(len(tuf.mirrorlist.mirrorlist_dict), 2)

    tuf.mirrorlist.remove_mirror()
    self.assertEqual(len(tuf.mirrorlist.mirrorlist_dict), 1)
    check_format = tuf.formats.MIRROR_SCHEMA.matches
    self.assertTrue(check_format(tuf.mirrorlist.mirrorlist_dict['mirror2']))


 





# RUN UNIT TESTS.
test_loader = tuf.tests.unittest_toolbox.unittest.TestLoader
suite = test_loader().loadTestsFromTestCase(TestMirrorlist)
tuf.tests.unittest_toolbox.unittest.TextTestRunner(verbosity=2).run(suite)

