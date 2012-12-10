#Jerry B. backer bataille16@gmail.com
#11/06/2012

#The purpose of this function is to interpose 
#on the trapped network calls (see src/libc for 
# network call trapping mechanism) and send the 
#calls to the TUFTranslator (see network_forwarder.py) to
#be processe This script should be run in a separate shell 
#before starting the legacy software updater processed

#usage: (on a separate shell) python socket_interposer.py 

import os,sys
import libnit_listener
from  network_forwarder import NetworkForwarder


def main():

        #make sure environmental variable for TUF_SUPPORT is ther 
        if os.environ.get("TUF_LEGACY") is  None:
          sys.exit("Cannot initiate TUF support. Try re-installing\n")
	#for now (testing purposes), we hardcode the server url
	# it can just as easily be passed as a command-line argument
	test = NetworkForwarder("http://localhost:8101")
	
	new_listener = libnit_listener.LibnitListener(test, debug_mode = True) 
   	#new_listener = libnit_listener.LibnitListener(test, debug_mode = False) 
   	new_listener.serve_forever()


if __name__ == "__main__":
	main()	
