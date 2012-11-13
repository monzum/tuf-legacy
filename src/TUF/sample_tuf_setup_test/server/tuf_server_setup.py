"""
<Program Name>
  tuf_server_setup.py

<Author>
  Konstantin Andrianov

<Started>
  November 9, 2012.

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  A quick way of setting up server-side updater framework.
  
<Procedures>

"""
import os
import quickstart


# SETUP

#  Create the project directories.
cwd = os.getcwd()
PROJECT_DIRECTORY = os.path.join(cwd, '..', 'project')



input_dict = {'expiration':'12/12/2013',
              'root':{'threshold':1, 'password':'pass'},
              'targets':{'threshold':1, 'password':'pass'},
              'release':{'threshold':1, 'password':'pass'},
              'timestamp':{'threshold':1, 'password':'pass'},
              'mirrorlist':{'threshold':1, 'password':'pass'}}

def _mock_prompt(message, junk=str, input_parameters=input_dict):
  if message.startswith('\nWhen would you like your certificates to expire?'):
    return input_parameters['expiration']
  for role in ['root', 'targets', 'release', 'timestamp', 'mirrorlist']: 
    if message.startswith('\nEnter the desired threshold for the role '+repr(role)):
      return input_parameters[role]['threshold']
    elif message.startswith('Enter the password for '+repr(role)):
      for threshold in range(input_parameters[role]['threshold']):
        if message.endswith(repr(role)+' ('+str(threshold+1)+'): '):
          return input_parameters[role]['password']
  print 'Cannot recognize message: '+message

# Monkey patching quickstart's _prompt() and _get_password.
quickstart._prompt = _mock_prompt
quickstart._get_password = _mock_prompt


# Finally create a server repository.
quickstart.build_repository(PROJECT_DIRECTORY)
