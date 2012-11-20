"""
<Program Name>
  tuf_client_api.py

<Purpose>
  Provide basic updater framework functionality.

<Author>
  Konstantin Andrianov
  Based on previously written module ('example_client.py') by Vladimir Diaz.

<Started>
  October, 20 2012

<Notes>
  Make sure tuf.conf contains correct repository location.

"""

import os
import logging
import tuf.conf
import tuf.mirrorlist
import tuf.client.updater

# Set logging. (Uncomment 'tuf.log.set_log_level(DEBUG)')
#tuf.log.set_log_level(logging.DEBUG)

# The local destination directory to save the target files.
TARGETS_DESTINATION_DIR = './targets'
tuf.conf.repository_directory = '.'



def update_mirrorlist(url):
  """
  <Purpose>
    Try to download latest version of mirrorlist metadata.

  <Arguments>
    url:
      A full url path from where mirrorlist.txt can be downloaded.
      ex: http://localhost:8101/metadata/mirrorlist.txt

    metadata_dir:
      Directory where all, latest client's metadata is located.
      This directory should contain 'root.txt', 'targets.txt',
      'release.txt', 'timestamp.txt' and 'mirrorlist.txt'.

      TODO: Delegations are not mentioned, yet.

  <Side Effects>
    A new mirrorlist file is downloaded and stored at {...}/metadata/current/
    directory.

  <Return>
    None.

  """
  
  if not url.endswith('mirrorlist.txt'):
    url +="/metadata/mirrorlist.txti"
  
  metadata_dir = os.path.join(tuf.conf.repository_directory, 'metadata')
  tuf.mirrorlist.update_mirrorlist(url, metadata_dir)





def get_mirrors():
  """
  <Purpose>
    Get the mirrors list.

  <Arguments>
    metadata_dir:
      Directory where all, latest client's metadata is located.
      This directory should contain 'root.txt', 'targets.txt',
      'release.txt', 'timestamp.txt' and 'mirrorlist.txt'.

      TODO: Delegations are not mentioned, yet.

  <Return>
    A list of mirrors that looks like this:
      [{mirror}]

  """

  # Get the path to the 'mirrorlist.txt'.
  metadata_dir = os.path.join(tuf.conf.repository_directory, 'metadata')
  current_dir = os.path.join(metadata_dir, 'current')
  mirrorlist_filepath = os.path.join(current_dir, 'mirrorlist.txt')

  # Extract mirrorlist dict from the 'mirrorlist.txt'.
  tuf.mirrorlist.load_mirrorlist_from_file(mirrorlist_filepath)
  return tuf.mirrorlist.mirrorlist_dict





def perform_an_update(target_path=None, 
                      destination_directory=TARGETS_DESTINATION_DIR):
  """
  <Purpose>
    Update metadata all metadata file, except 'mirrorlist.txt'.
    Update modified and/or dowload newly added target files, performing
    all necessary security checks on them.

  <Arguments>
    target_path:
      Specific target file to download.  In this case only 'target_path' file
      will be downloaded, not all the targets that were updated.  'target_path' 
      should be relative to the value (which is a directory) of the 
      'targets_path' key of the mirror's dictionary, like 'targets'.

    destination_directory:
      A directory where the target files are stored/saved.

  <Side Effects>
    All metadata files are updated with previous versions of metadata saved
    at {...}/metadata/previous/ directory.  Target file(s) are downloaded and
    stored at the 'destination_directory'.

  <Return>
    None.

  """
  # Create the repository object using the repository name 'repository'
  # and the repository mirrors.
  repository_mirrors = get_mirrors()
  repository = tuf.client.updater.Repository('repository', repository_mirrors)
  targets = []

  # Refresh the repository's top-level roles, store the target information for
  # all the targets tracked, and determine which of these targets have been
  # updated.
  repository.refresh()
  
  if target_path is not None:
    target = repository.target(target_path)
    targets.append(target)

  else:
    targets = repository.all_targets()
 
  updated_targets = repository.updated_targets(targets, 
                                               destination_directory)

  # Download each of these updated targets and save them locally.
  for target in updated_targets:
    repository.download_target(target, destination_directory)
