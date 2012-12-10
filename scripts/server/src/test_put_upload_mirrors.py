import httplib
conn = httplib.HTTPConnection("127.0.0.1:8101")
conn.set_debuglevel(10)
conn.putrequest('PUT',"/legacy-app-lib/moo.txt")
new_string = "haha"
conn.putheader("Content-Length", len(new_string))
conn.endheaders()
conn.send(new_string)
resp = conn.getresponse()
data = resp.read()
print data
