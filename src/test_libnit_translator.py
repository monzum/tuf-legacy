#test mechanism for libnit_listener and tuf api translator

import libnit_listener
from  tuf_api_translator import TUFTranslator

def main():
	test = TUFTranslator("127.0.0.1")
	new_listener = libnit_listener.LibnitListener(test, debug_mode = True) 
   	new_listener.serve_forever()


if __name__ == "__main__":
	main()	
