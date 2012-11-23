#Jerry B. backer
#11/06/2012
#test for TUFTanslator and libnit_lister
#Uses test_simple server
import sys
sys.path.append("../src") #hardcoded for testing purposes

import libnit_listener
from  tuf_api_translator import TUFTranslator

def main():
	test = TUFTranslator("http://localhost:8101")
	new_listener = libnit_listener.LibnitListener(test, debug_mode = True) 
   	new_listener.serve_forever()


if __name__ == "__main__":
	main()	
