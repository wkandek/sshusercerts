import http.server
import syslog
import os
import urllib
import pyotp
import pwd
import pam
import datetime
import time
import crypt
import subprocess
import pyqrcode
import png


programname = "User Cert Service"
try:
	maxlen = int(os.environ["MAXMSGLEN"])
except:
	maxlen = 2048
try:
	certname = os.environ["CERTNAME"] 
except:
	certname = "demo_ssh_user_ca"
try:
	if (os.environ["DEMOMODE"].lower() == "true"):
		demomode = True
	else:
		demomode = False
except:
	demomode = False 

SUCCESS = 0
USERNOTFOUND = 1
USERIDNOTAPPLICABLE = 2
PASSWORDERROR = 3
OTPERROR = 4

with open(certname+".pub", "r") as f:
	pubcert = f.read()
	f.close()


def tauth(user, passwd, pin):

	starttime = datetime.datetime.now()
	rc = SUCCESS
	try:
		ps = pwd.getpwnam(user)
	except:
		rc = USERNOTFOUND

	if rc == SUCCESS:
		if ps.pw_uid >= 1000:
			p = pam.pam()
			if p.authenticate(user, passwd):
				seed = ""
				if "OTP=" in ps.pw_gecos:
					seed = ps.pw_gecos[ps.pw_gecos.find("OTP=")+4:ps.pw_gecos.find("OTP=")+20:] 
				else:
					seed = ps.pw_gecos
				if len(seed) == 16:
					try:	
						totp = pyotp.TOTP(seed)
					except:
						rc = OTPERROR  
				else:
					rc = OTPERROR
				if rc == SUCCESS:
					if pin != totp.now():
						rc = OTPERROR 
			else:
				rc = PASSWORDERROR 
		else:
			rc = USERIDNOTAPPLICABLE
	# if en error happen try to assure that timing is constant - password is much slower than others
	if rc != SUCCESS:
		endtime = datetime.datetime.now()
		deltatime = endtime - starttime
		time.sleep(abs(5000.0 - deltatime.total_seconds() * 1000.0)/1000.0)
	return(rc)

	
def chpasswd(user, passwd):
    proc = subprocess.Popen(
        ['/usr/sbin/chpasswd'], 
        stdin = subprocess.PIPE, 
        stdout = subprocess.PIPE, 
        stderr = subprocess.PIPE
    )
    out, err = proc.communicate(bytes(user + ':' + passwd, "utf-8"))
    proc.wait()

    if proc.returncode != 0:
        print( "Error: Return code", proc.returncode, ", stderr: ", out, err )
        if out:
            syslog.syslog("stdout: " + out)
        if err:
            syslog.syslog("stderr: " + err)
    return(proc.returncode)
	
	
def adduser( user, password, otpid ):
	cmdstr = "/usr/sbin/useradd -d /home/genericuser -s /bin/rbash -M -N -c OTP=%s %s" % (otpid, user)
	systemrc = os.system(cmdstr)      
	syslogmsg = programname+" RC:"+str(systemrc)+" "+cmdstr
	syslog.syslog(syslogmsg)
	rc = chpasswd( user, password )
	syslogmsg = programname+" Adduser Error: " + user + " " + str(rc)
	syslog.syslog(syslogmsg)
	print(syslogmsg)
	return(rc)


class Server(http.server.BaseHTTPRequestHandler):

	def do_HEAD(self):
		return

	def do_GET(self):
		status = 200
		content_type = "text/html"
		if demomode and "adduser" in self.path:
			seedcode = pyotp.random_base32()
			response_content = "<HTML><TITLE>Adduser</TITLE><BODY><FORM METHOD=POST>User: <INPUT NAME=user TYPE=text LENGTH=40><BR>Pass: <INPUT NAME=pass TYPE=text LENGTH=40><br>OTP Id: <INPUT NAME=otpid TYPE=text VALUE="+str(seedcode)+"> Id created randomly and creates below QR code, if edited will not match anymore<br>then use the code itself to create the new autenticator instance<BR><BR><INPUT TYPE=SUBMIT></FORM>"
			response_content = response_content + "<BR>Here is the public key needed to install on your demo server:"
			response_content = response_content + "<BR><BR>" + pubcert
			response_content = response_content + "<BR><BR>Put it in a file and add the TrustedUserCAKeys <filename> in the /etc/ssh/sshd_config file, then restart sshd.<br><br>"
			qrcodestr = "otpauth://totp/demosshusercerts@example.com?secret="+str(seedcode)+"&issuer=DemoSSHUserCerts"
			qrcode = pyqrcode.create(qrcodestr)
			image_as_str = qrcode.png_as_base64_str(scale=5)
			response_content = response_content + '<IMG ALIGN=left SRC="data:image/png;base64,{}">'.format(image_as_str)
			response_content = response_content + "</BODY></HTML>"
		else:
			response_content = "<HTML><TITLE>Sign</TITLE><BODY><FORM METHOD=POST>User: <INPUT NAME=user TYPE=text LENGTH=40><br>Pass: <INPUT NAME=pass TYPE=password LENGTH=40><br>PIN: <INPUT NAME=pin TYPE=text><br><TEXTAREA NAME=key>Key:</TEXTAREA><INPUT TYPE=SUBMIT></FORM></BODY></HTML>"
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
				if demomode and "adduser" in self.path:
					# adduser caseuser
					user = postvars["user"]
					password = postvars["pass"]
					otpid = postvars["otpid"]
					rc = adduser( user, password, otpid )
					if rc == 0:
						response_content = "Success User added"
					else:
						response_content = "Error User not added"
				else:
					sshkey = postvars["key"]
					if ("ssh-rsa" in sshkey) or ("ssh-dss" in sshkey) or ("ecdsa-sha2-nistp256" in sshkey) or ("ssh-ed25519" in sshkey):
						# process the key
						uname = postvars["user"]
						passwd = postvars["pass"]
						pin = postvars["pin"]
						rc = tauth( uname, passwd, pin )
						if rc == 0:
							uname = uname.replace( " ", "+" )
							uname = "+"+uname+"@"
							newuname = uname.replace( "+", " " )
							sshkey = sshkey.replace( "ssh-rsa+", "ssh-rsa " )
							sshkey = sshkey.replace( "ssh-dss+", "ssh-dss " )
							sshkey = sshkey.replace( "ecdsa-sha2-nistp256+", "ecdsa-sha2-nistp256 " )
							sshkey = sshkey.replace( "ssh-ed25519+", "ssh-ed25519 " )
							sshkey = sshkey.replace( uname, newuname )

							fname = postvars["user"]
							with open(fname, "w") as f:
								f.write(sshkey)
								f.close()

							# delete old certfile
							certfname = fname+"-cert.pub"
							try:
								os.remove(certfname)
							except:
								pass

							cmdstr = "/usr/bin/ssh-keygen -s %s -I user_%s_cert -n %s -V +1h ./%s" % (certname, fname, fname, fname)
							systemrc = os.system(cmdstr)      
							syslogmsg = programname+" RC:"+str(systemrc)+" "+cmdstr
							syslog.syslog(syslogmsg)
							print(syslogmsg)

							response_content = "test" 
							with open(certfname, "r") as f:
								response_content = f.read()
								f.close()
				
						else:
							syslogmsg = programname+" Auth Error: "+str(rc)
							syslog.syslog(syslogmsg)
							print(syslogmsg)
							status = 403
					else:
						syslogmsg = programname+" SSH Key format error: 415"
						syslog.syslog(syslogmsg)
						print(syslogmsg)
						status = 415
			else:
				syslogmsg = programname+" Request too large: 431"
				syslog.syslog(syslogmsg)
				print(syslogmsg)
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

