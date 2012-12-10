import socket
import hashlib
import time


# generate md5 of manifest file
def manifestfile(path):

    manifest = open(path,'rb')
    
    m = hashlib.md5()
    
    content = manifest.read()

    # if content is null, return None
    if not content:
        return None

    m.update(content)

    manifest.close()

    return m.hexdigest()



# current datetime
def now():

    return time.strftime('%m-%d-%Y %H:%M:%S',time.localtime(time.time()))



if __name__ == '__main__':

    # initial socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # bind local port 8001
    sock.bind(('localhost', 8102))

    # listening , support 3 socket connections
    sock.listen(3)

    i=0
    
    while True:
        i=i+1
        print i

        # generate md5
        checkvalue = manifestfile('./MANIFEST')
        print now()+':compute file md5'
        print checkvalue

        # waiting for connection, and create connection,address list()
        print now()+':waiting for connection...'
        connection,address = sock.accept()
        

        try:
            # setup timeout time
            connection.settimeout(60)

            # receive data from mirror
            recvdata = connection.recv(1024)

            print 'Now server is exchanging data with ' + recvdata 

            # Send server manifest md5 value to mirror
            connection.send(checkvalue)
            print now()+':checkvalue sends out'

            # close connection
            connection.close()
            print now()+':connection closes'

        except socket.timeout:
            print now()+':time out'

    print "end"
