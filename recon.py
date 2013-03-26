import sys
import optparse
import ConfigParser
import logging
import time

logging.basicConfig(level=logging.INFO)

import dns
import track
import flash
import database

VERSION = '1.0'

class Recon:

	def __init__(self):
		self.options = self.loadOptions()
		self.config = self.loadConfig(self.options.config_file)

	def Run(self):

		db = database.Worker()
		db.start()

		dw = dns.Worker()
		dw.start()

		trt = track.Worker("TCP")
		trt.start()

		tru = track.Worker("UDP")
		tru.start()

		fl = flash.Worker()
		fl.start()

	def loadOptions(self):
		parser = optparse.OptionParser(version=VERSION)
		parser.add_option('-c', dest='config_file', help='Configuration file location')
		parser.add_option('-d', dest='daemonize', help='Daemonize process')
		(options, args) = parser.parse_args()
		if not options.config_file:
			parser.print_help()
			sys.exit(1)
		return options

	def loadConfig(self, config_file):
		try:
			fp = open(config_file)
		except IOError as e:
			logging.warning("No such configuration file: %s" % (config_file))
			sys.exit(1)

		config = ConfigParser.SafeConfigParser()
		config.readfp(fp)
		if "General" not in config.sections():
			logging.warning("No \"General\" section in configuration file")
			sys.exit(1)
		return config

if __name__ == "__main__":
	server = Recon()
	server.Run()

