"""
<Program Name>
  update_client.py

<Author>
  Konstantin Andrianov

<Started>
  October 27, 2012

<Purpose>
  Update metadata all metadata file, except 'mirrorlist.txt'.
  Update modified and/or dowload newly added target files, performing
  all necessary security checks on them.

"""

import tuf_client_api as client

client.perform_an_update()
