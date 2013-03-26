import multiprocessing as mp
import logging
import sys
import socket
import time
import struct
import threading
import SocketServer

logger = logging.getLogger("flash_policy")

class TCPPacketHandler(SocketServer.BaseRequestHandler):

	def handle(self):
		self.data = self.request.recv(1024).strip()
		logger.info("Got flash policy packet from %s", self.client_address[0])
		print self.data
		if '<policy-file-request/>' in self.data:
			print 'received policy'
			self.request.send('<?xml version="1.0"?><cross-domain-policy><allow-access-from domain="r.0x0a.net" to-ports="20000" /></cross-domain-policy>')
		self.request.close()

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

class Worker:
	__proc = None
	__running = True

	def __init__(self):
		self.__proc = mp.Process(target=self.loop)
		self.__proc.daemon = False
		
		self.port = 843
		self.host = 'localhost'

		self.server = ThreadedTCPServer((self.host, self.port), TCPPacketHandler)

		self.thread = threading.Thread(target=self.server.serve_forever)
		self.thread.setDaemon(True)

	def start(self):
		self.__proc.start()

	def stop(self):
		self.__running = False
		self.server.shutdown()
		self.__proc.join()

	def loop(self):
		self.thread.start()

		while self.__running:
			time.sleep(5)

