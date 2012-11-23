tuf-legacy
==========

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
          As discussed in updateframerwork.com/wiki/Docs/Security, there are numerous security flaws with          this current approach. TUF reduces many of these security flaws through various checks.
          
          However, adding TUF to application x requires modification to x codebase; This may be cumbersom          for software developers, as well as users of legacy applications.
           
           Our work provides a layer that works between aplication x and TUF to provide the security
	   features of TUF, without the need to modify x

Approach: The main idea behind our approach is to intercept ALL network calls of the application x, 
	  forward the ones not related to software updating, and process the ones related to software
	  updating through TUF api. This MUST be done in transparent fashion.

Mechanism:
		- Network call trapping and interposing

		- Classifying of network calls
	
		- Translating relevant network calls to TUF API

		- Return requested updated transparently to software updater




Components for testing: To test our proposed work, we need to simulate the servers, mirrors, and the client (legacy application)

To setup for test, see setup.txt
