import urllib2
import urllib
#response = urllib2.urlopen("http://www.google.com")
response = urllib.urlretrieve("http://www.google.com", filename = "update_file2.txt")

#update_file = open("update_file.txt", 'w')

#update_file.write(response.read())
#update_file.close()
