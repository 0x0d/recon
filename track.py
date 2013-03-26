import multiprocessing as mp
import logging
import sys
import socket
import time
import struct
import threading
import SocketServer

logger = logging.getLogger("tracker")

class TCPPacketHandler(SocketServer.BaseRequestHandler):

	def handle(self):
		self.data = self.request.recv(1024).strip()
		logger.info("Got TCP packet from %s", self.client_address[0])
		print self.data
		#self.request.send(self.data.upper())
		self.request.close()

class UDPPacketHandler(SocketServer.BaseRequestHandler):

	def handle(self):
		self.data = self.request[0].strip()
		self.socket = self.request[1]
		logger.info("Got UDP packet from %s", self.client_address[0])
		print self.data
		#self.request.send(self.data.upper())

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

class ThreadedUDPServer(SocketServer.ThreadingMixIn, SocketServer.UDPServer):
    pass

class Worker:
	__proc = None
	__running = True

	def __init__(self, type):
		self.__proc = mp.Process(target=self.loop)
		self.__proc.daemon = False
		
		self.port = 20000
		self.host = 'localhost'

		global logger
		logger = logging.getLogger("tracker %s" % (type))

		if type == "TCP":
			self.server = ThreadedTCPServer((self.host, self.port), TCPPacketHandler)
		elif type == "UDP":
			self.server = ThreadedUDPServer((self.host, 20001), UDPPacketHandler)

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

