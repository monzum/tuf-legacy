#!/usr/bin/env python
# Copyright 2010 The Update Framework.  See LICENSE for licensing information.

import os

from tuf.client import updater

myrepo = updater.Repository("myrepo")

myrepo.refresh()

myrepo.get_all_targets()

print myrepo.get_all_targets()[0]

dest_path = "./downloaded_example.py"

if os.path.exists(dest_path):
    os.remove(dest_path)

myrepo.get_all_targets()[0].download(dest_path)
