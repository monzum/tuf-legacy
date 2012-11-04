#! /usr/bin/env python

from distutils.core import setup


from tuf.build_updater import *

setup(  name='hello',
        version='0.0',
        description='test',
        author='me',
        author_email='me@there.com',
        url='http://place.org',
        py_modules=['hello'],
        cmdclass={'build_updater':build_updater, 'update_updater':update_updater, 'update':update})
