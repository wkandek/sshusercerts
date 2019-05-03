from http.server import BaseHTTPRequestHandler
from syslog import syslog
from os import system 
import urllib
import multipart

programname = "User Cert Service"
maxlen = 2048

class Server(BaseHTTPRequestHandler):
	def do_HEAD(self):
		return

	def do_GET(self):
		status = 200
		content_type = "text/html"
		response_content = "<HTML><BODY><FORM METHOD=POST>User: <INPUT NAME=user TYPE=text LENGTH=40><br>Pass: <INPUT NAME=pass TYPE=text LENGTH=40><br>PIN: <INPUT NAME=pin TYPE=text><br><TEXTAREA NAME=key>Key:</TEXTAREA><INPUT TYPE=SUBMIT></FORM></BODY></HTML>"
		self.send_response(status)
		self.send_header('Content-type', content_type )
		self.end_headers()
		content = bytes(response_content, "UTF-8")
		self.wfile.write(content)


	def do_POST(self):
		status = 200
		content_type = "text/html"
		response_content = ""

		if self.headers['content-type'] == "application/x-www-form-urlencoded":
			length = int(self.headers['content-length'])
			if (length < maxlen):
				qs = self.rfile.read(length)
				qsd = urllib.parse.unquote(qs.decode())
				l = qsd.split("&")
				postvars = dict(s.split("=") for s in l )
				sshkey = postvars["key"]
				if ("ssh-ra" in sshkey):

					# process the key
					uname = postvars["user"]
					uname = uname.replace( " ", "+" )
					uname = "+"+uname+"@"
					newuname = uname.replace( "+", " " )
					sshkey = sshkey.replace( "ssh-rsa+", "ssh-rsa " )
					sshkey = sshkey.replace( uname, newuname )

					fname = postvars["user"]
					with open(fname, "w") as f:
						f.write(sshkey)
						f.close()
					#colist = [ "/usr/bin/ssh-keygen", "-s ssh_ca" ]
					#colist.append( "-I user_%s_cert" % fname)
					#colist.append( "-n %s" % fname)
					#colist.append( "-V +1d" )
					#colist.append( "./%s" % fname)
					#sshkeygenoutput = subprocess.check_output( colist )
					#print(sshkeygenoutput.result)

					# delete old certfile
					certfname = fname+"-cert.pub"
					os.remove(certfname)

					cmdstr = "/usr/bin/ssh-keygen -s ssh_user_ca -I user_%s_cert -n %s -V +1h ./%s" % (fname,fname, fname )
					systemrc = system(cmdstr)      
					syslogmsg = programname+" RC:"+str(systemrc)+" "+cmdstr
					syslog(syslogmsg)
					print(systemrc)

					response_content = "test" 
					with open(certfname, "r") as f:
						response_content = f.read()
						f.close()
			
				else:
					syslogmsg = programname+" SSH Key format error: 415"
					syslog(syslogmsg)
					status = 415
			else:
				syslogmsg = programname+" Request too large: 431"
				syslog(syslogmsg)
				status = 431
			
		elif self.headers['content-type'] == "multipart/form-data":
			postvars = {}
			response_content = "mp test" 
		else:
			postvars = {}
			response_content = "nothing" 

		self.send_response(status)
		self.send_header('Content-type', content_type )
		self.end_headers()
		content = bytes(response_content, "UTF-8")
		self.wfile.write(content)

