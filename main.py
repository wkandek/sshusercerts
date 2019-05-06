import time
from http.server import HTTPServer
from server import Server

HOST_NAME = '0.0.0.0'
PORT_NUMBER = 8080

if __name__ == '__main__':
	httpd = HTTPServer((HOST_NAME, PORT_NUMBER), Server)
	print( time.asctime(), 'Server Up - %s:%s,' % (HOST_NAME, PORT_NUMBER))
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		pass
	httpd.server_close()
	print( time.asctime(), 'Server Down - %s:%s,' % (HOST_NAME, PORT_NUMBER))
