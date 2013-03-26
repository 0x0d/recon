import multiprocessing as mp
import MySQLdb
import os
import logging

logger = logging.getLogger("db")

class Worker:

	__proc = None
	__running = True

	def __init__(self):
		self.__queue = mp.Queue()
		self.__proc = mp.Process(target=self.loop)
		self.__proc.daemon = False
		self.conn = None
		self.cursor = None
		self.db_user = "recon"
		self.db_password = ""
		self.db_name = "recon"
		self.db_sock = "/tmp/mysql.sock"

	def start(self):
		self.connect()
		self.__proc.start()

	def stop(self):
		self.push(self._stop)
		self.proc.join()

	def push(self, command):
		self.__queue.put(command, block=False)

	def connect(self):
		try:
			self.conn = MySQLdb.connect(user=self.db_user, passwd=self.db_password, unix_socket=self.db_sock);
			self.select_db(self.db_name)
			self.cursor = self.conn.cursor()

		except MySQLdb.Error, e:
			print "Mysql error during db connect: %d: %s" % (e.args[0], e.args[1])

	def loop(self):
		while True:
			command = self.__queue.get()
			if command == self._stop:
				break
			self.process(command)

	def select_db(self, db):
		try:
			self.conn.select_db(db);
		except MySQLdb.Error, e:
			print "Mysql error during db select: %d: %s" % (e.args[0], e.args[1])

	def process(self, statement):

		try:
			self.cursor.execute(query)
		except (AttributeError, MySQLdb.OperationalError):
			self.connect()
			self.cursor.execute(query)
		except MySQLdb.Error, e:
			print "Mysql error during executing query: %d: %s" % (e.args[0], e.args[1])

	def escape(self, string):
		return self.conn.escape_string(string)

