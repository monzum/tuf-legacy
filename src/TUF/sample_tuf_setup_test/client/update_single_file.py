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
import sys
import tuf_client_api as client

print sys.argv[1]
client.perform_an_update(sys.argv[1])
