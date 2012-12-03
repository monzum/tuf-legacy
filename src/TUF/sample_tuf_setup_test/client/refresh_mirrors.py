"""
<Program Name>
  test_mirrorlist.py

<Author>
  Konstantin Andrianov

<Started>
  October 27, 2012

<Purpose>
  Update 'mirrorlist.txt' metadata.

"""

import tuf_client_api as client

URL = 'http://localhost:8101/metadata/mirrorlist.txt'

client.update_mirrorlist(URL)
