#! /usr/bin/env python

import logging

import tuf.client.updater

# Uncomment the line below to enable the printing of debugging information.
#tuf.log.set_log_level(logging.DEBUG)

# Set the local repository directory containing all of the metadata files.
tuf.conf.repository_directory = './local-repository'

# Set the repository mirrors.  This dictionary is needed by the repository
# class of updater.py.
repository_mirrors = {'mirror1': {'url_prefix': 'http://localhost:8001',
                                  'metadata_path': 'metadata',
                                  'targets_path': 'targets',
                                  'confined_target_paths': ['']}}

# Create the repository object using the repository name 'repository'
# and the repository mirrors defined above.
repository = tuf.client.updater.Repository('repository', repository_mirrors)

# The local destination directory to save the target files.
destination_directory = './targets'

# Refresh the repository's top-level roles, store the target information for
# all the targets tracked, and determine which of these targets have been
# updated.
repository.refresh()
all_targets = repository.all_targets()
updated_targets = repository.updated_targets(all_targets, destination_directory)

# Download each of these updated targets and save them locally.
for target in updated_targets:
  repository.download_target(target, destination_directory)

# Remove any files from the destination directory that are no longer being
# tracked.
repository.remove_obsolete_targets(destination_directory)

"""
repository.refresh()
targets_of_role1 = repository.targets_of_role('targets/role1')
updated_targets = repository.updated_targets(targets_of_role1, destination_directory)

for target in updated_targets:
  repository.download_target(target, destination_directory)
"""

"""
repository.refresh()
target = repository.target('helloworld.py')
updated_target = repository.updated_targets([target], destination_directory)

for target in updated_target:
  repository.download_target(target, destination_directory)
"""
