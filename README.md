test-dist for tuf-legacy

Goal:Incorporate The Update Framework (TUF) into legacy applications.
     TUF provides a secure approach for software updaters
     to contact servers and mirrors and perform updates. 
     For more information about TUF, go to : https://www.updateframework.com

     Integrating TUF onto software updaters require some level of coding of the  
     updater (recomplilation and redeployment). We propose a mechanism to minimize
     (or remove) the additional code of integrating TUF in software updaters.
 

Scenario: An application x has a built-in software updater that (from time to time) polls its server
          to see if any of its files need to be updated. If so, the software updater contacts available
	  mirrors(s) and perform the necessary updates. 
          As discussed in updateframerwork.com/wiki/Docs/Security, there are numerous security flaws with this current 
          approach. TUF reduces many of these security flaws through various checks. However, adding TUF to 
          application x requires modification to x codebase;  this may be cumbersome for software developers,
          as well as users of legacy applications. Our work provides a layer that works between aplication x and TUF
          to provide the security features of TUF, without the need to modify x.

Approach: The main idea behind our approach is to intercept ALL network calls of the application x, 
	  forward the ones not related to software updating, and process the ones related to software
	  updating through TUF api. This MUST be done in transparent fashion.

Mechanism:

		- Intercept network calls of legacy-application
			- Use LD_PRELOAD to load a modified subsection of libc (socket functions)
			- Make the modified libc trap network calls of legacy application
	
		- Translate relevant network calls to TUF API
			- Forward network calls that are not for software update purposes
			- Wrap the ones that are for software update with tuf-related calls 
			  for security checks and download requested  file(s)

		- Return requested updated transparently to software updater
		

Components for testing:
		
		legacy-client: src/legacy-client
				the legacy application (with built-in software updater). 
				The main file performs all the necessary work. 
				 The dir src/legacy-client/client handles the TUF related work when 
				  the network interposer is enabled
	
		server: src/server-resources
				the server.py runs an HTTP server on localhost.
					
		mirrors: src/mirrors
			For now we have three mirrors running on ports 8000-8002



#####
Setup:
	Setup requires every components of the platform  without TUF(server, mirrors, client) as well as the network interposing mechanism when TUF supported updates are desired.
Many terminal tabs are thus needed to simulate the whole platform.
Go to the application dir and get the tuf-legacy.tar.gz file
	
	tar xvf tuf-legacy.tar.gz
	
	#Setting up the different components 
	server-setup:
		#Open a new terminal tab and cd to base dir of application (tuf-legacy-dist)
		cd server-resources
		python server.py
		#When TUF is enabled the server makes use of metadata/ and client/ dirs

	mirrors-setup:
		#We need at least 1 mirror to run the project.
		#For each mirror:
			#Open a new terminal tab and cd to base dir of application (tuf-legacy-dist)
			cd mirrors/mirror[i]/files    #where [i] is 1, 2 or 3)
			python ../mirror[i].py #run the specic mirror from the files dir where targets are

	client-setup:
		#The client can be setup with tuf enabled-support or without	
		#For client initialization without TUF:
		#Open a new  terminal tab and cd to base dir of application(tuf-legacy-dist)
		cd legacy-client
		python legacy-client.py

		#To enable TUF-support:
			1.#Setup the network interpose listener to re-direct necessary calls to TUF
			   #Open a  tab and cd to the base dir of application (tuf-legacy-dist)
			  python socket_interposer.py 
			2.#Use LD_PRELOAD to interpose network calls of the client application
			  #Open a tab and cd to the base dir of the application (tuf-legacy-dist)
			   cd libc
			   . load_shim_proxy.sh  #load new libc on current terminal
			   cd ../legacy-client
			   python legacy-client.py #now client is running with TUF support


The setup must be followed in the order provided above
For now, the main interaction is to be done through the legacy-client options


LIMITATIONS:
	(When running client without TUF-support)
	The repository maintains the files to be updated in server-resources/legacy-app/lib.
	If the admin modifies any of files in that dir, we provide make_manifest.py (in server-resources)
	to update the MANIFEST file to illustrate changes made to the file. However, we haven't figured
	out an efficient way to push the changed files (and manifest) to the mirrors. We are 
	investigating how to resolve this situation.
	
	We also are investigating how to resolve this situation with TUF-enabled
	Along with updating the mirrors with the updated files, we must  update many of the metadata 
	that TUF uses (using through TUF/src/quickstart.py) and pushing the updated metadata
	(in client/ dir) to the legacy-client
	
