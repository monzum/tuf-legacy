#! /usr/bin/env python

import os

import tuf
from tuf.client import updater

tuf.conf.settings.repo_meta_dir = "."
repo_data = {'repo': {'urlbase': 'http://localhost:8001', 'metapath': "meta", 'targetspath': "targets", 'metacontent': ['**'], 'targetscontent': ['**']}}

repo = updater.Repository("", repo_data)

repo.refresh()
targets = repo.get_all_targets()
files_to_update = repo.get_files_to_update(targets)
for target in targets:
	if target in files_to_update:
		target.download(target.path.split(os.path.sep)[-1])
