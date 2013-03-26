import multiprocessing as mp
import logging
import sys
import socket
import time
import struct
import threading
import SocketServer

logger = logging.getLogger("dns")

class dns_error(Exception):
	pass

class DNSPacketHandler(SocketServer.BaseRequestHandler):

	def handle(self):
		rcode = 0
		rdata = []
		ns_resource_records = []
		ar_resource_records = []
		response = '85.17.93.121'

		data = self.request[0].strip()
		socket = self.request[1]
		
		logger.info("Got UDP packet from %s:%d" % (self.client_address[0], self.client_address[1]))
		try:
			qid, question, qtype, qclass = self.parse_request(data)
		except dns_error as e:
			logger.error("Could not parse query ")
			rcode = 3
			return

		question = map(lambda x: x.lower(), question)

		if rcode == 0:
			logger.info("Got DNS %s request for %s" % (qtype, '.'.join(question)))
			rdata = struct.pack("!I", self.ipstr2int(response))

		logger.info("Sending anwser with rcode:%d to %s:%d" % (rcode, self.client_address[0], self.client_address[1]))
		resp_pkt = self.format_response(qid, question, qtype, qclass, rcode,
			[{'qtype': qtype, 'qclass': qclass, 'ttl': 14400, 'rdata': rdata}], # Answer section
			[], # NS section, rdata = labels2str(value.split("."))
			[] # Additional section
		)
		socket.sendto(resp_pkt, self.client_address)

	def label2str(self, label):
		s = struct.pack("!B", len(label))
		s += label
		return s

	def labels2str(self, labels):
		s = ''
		for label in labels:
			s += self.label2str(label)
		s += struct.pack("!B", 0)
		return s

	def ipstr2int(self, ipstr):
		ip = 0
		i = 24
		for octet in ipstr.split("."):
			ip |= (int(octet) << i)
			i -= 8
		return ip

	def parse_request(self, packet):
		hdr_len = 12
		header = packet[:hdr_len]
		qid, flags, qdcount, _, _, _ = struct.unpack('!HHHHHH', header)
		qr = (flags >> 15) & 0x1
		opcode = (flags >> 11) & 0xf
		rd = (flags >> 8) & 0x1
		#print "qid", qid, "qdcount", qdcount, "qr", qr, "opcode", opcode, "rd", rd
		if qr != 0 or opcode != 0 or qdcount == 0:
			raise dns_error("Invalid query")
		body = packet[hdr_len:]
		labels = []
		offset = 0
		while True:
			label_len, = struct.unpack('!B', body[offset:offset+1])
			offset += 1
			if label_len & 0xc0:
				raise dns_error("Invalid label length %d" % label_len)
			if label_len == 0:
				break
			label = body[offset:offset+label_len]
			offset += label_len
			labels.append(label)
		qtype, qclass= struct.unpack("!HH", body[offset:offset+4])
		if qclass != 1:
			raise dns_error("Invalid class: " + qclass)
		return (qid, labels, qtype, qclass)

	def format_response(self, qid, question, qtype, qclass, rcode, an_resource_records, ns_resource_records, ar_resource_records):
		resources = []
		resources.extend(an_resource_records)
		num_an_resources = len(an_resource_records)
		num_ns_resources = num_ar_resources = 0
		if rcode == 0:
			resources.extend(ns_resource_records)
			resources.extend(ar_resource_records)
			num_ns_resources = len(ns_resource_records)
			num_ar_resources = len(ar_resource_records)
		pkt = self.format_header(qid, rcode, num_an_resources, num_ns_resources, num_ar_resources)
		pkt += self.format_question(question, qtype, qclass)
		for resource in resources:
			pkt += self.format_resource(resource, question)
		return pkt

	def format_header(self, qid, rcode, ancount, nscount, arcount):
		flags = 0
		flags |= (1 << 15)
		flags |= (1 << 10)
		flags |= (rcode & 0xf)
		hdr = struct.pack("!HHHHHH", qid, flags, 1, ancount, nscount, arcount)
		return hdr

	def format_question(self, question, qtype, qclass):
		q = self.labels2str(question)
		q += struct.pack("!HH", qtype, qclass)
		return q

	def format_resource(self, resource, question):
		r = ''
		r += self.labels2str(question)
		r += struct.pack("!HHIH", resource['qtype'], resource['qclass'], resource['ttl'], len(resource['rdata']))
		r += resource['rdata']
		return r

class ThreadedUDPServer(SocketServer.ThreadingMixIn, SocketServer.UDPServer):
    pass

class Worker:
	__proc = None
	__running = True

	def __init__(self):
		self.__proc = mp.Process(target=self.loop)
		self.__proc.daemon = False

		self.host = '127.0.0.1'
		self.port = 53

		self.server = ThreadedUDPServer((self.host, self.port), DNSPacketHandler)
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
