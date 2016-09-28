#! /usr/bin/python

# TCZee - Scapy-based TCP stack basic implementation for network testing 
# Copyright (C) 2015 Marco Zunino

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# version 2 as published by the Free Software Foundation

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# A copy of the full GNU General Public License is available in 
# the LICENSE file in the root folder of the original projecti
# hosted on 'https://github.com/zupino/tcz'.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# This file is part of the Integratio Project, a complete system test solution
# designed to run on a portable development board (as Raspberry Pi, BeagleBone or similar)
# and to provide a platform for the Integratio Test Suite, a collection of test cases to stress
# IoT product client functionalities while in condition of networking error or other corner cases
# that would be extremely difficult to reproduce on the real environment.

# This file is designed to run on a modified version of the Raspian operative system.
# The Raspberry device act as WiFi Access Point, DNS server and Web Server,
# providing answer to the requests of the tested IoT product in such a way to
# stress the desired error condition.

#
#
#   ##         #
#   # #        #
#   #  #  ###  ###  #   #  ###
#   #  #  ##   #  # #   # #   #
#   ###   ###  ###   ###   ###
#                            #
#                          # #
#                           #
#
#   Load the script in scapy and manually create the
#   TCZee object
#
#      log_interactive.setLevel(1)
#      t = tcz.TCZee(80, debug=x)
#      t.run()
#
#   Also, remember to block RST packet from the server machine with the following iptable rule
#
#	iptables -A OUTPUT -p tcp --tcp-flags RST RST -j DROP
#
#

from scapy.all import *
# from tcz import TCPConnection
import time
import sys
import signal
from functools import wraps
# Just a small utility to get from system the ip of a specific network interface
import socket
import fcntl
import struct
import threading

from Queue import Queue
from threading import Thread


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

# get_ip_address('eth0')
# '38.113.228.130'


# With the stunnel configuration, we need again the possibility
# to work on the loopback interface
conf.L3socket = L3RawSocket

class TCZee(Automaton):
        def parse_args(self, jsonConfig={}, **kargs):
                # DEBUG	
		#print "[DEBUG] Starting processing parameters"	
		Automaton.parse_args(self, **kargs)
		if 'listeningPort' in jsonConfig:
			self.sport = int( jsonConfig['listeningPort'] )
		else:
			self.sport = 80
		self.dport = 0
		self.responseReady = 0
		self.synAckReady = 0
		self.myIp = 0

		self.curAck = 0
		self.curSeq = 0

                # BD:28-09-16 #Issue16 
                # Handling multi TCP conn using dictionary for holding the
                # curAck and curSeq states.
                self.curAckHash={}
                self.curSeqHash={}

		# recv and send buffer to be used by the external     httz component
		self.recv = Queue()
		self.toSend = ""
		self.jsonConfig=jsonConfig

		# Keeping track of the last valid packet received
		self.lastReceived = ""
		
		if 'listeningInterface' in self.jsonConfig:

			self.interface = str( self.jsonConfig['listeningInterface'] )
		else:
			self.interface = ""
		
                # We are assuming here that IntegratioWebServer is listening on wlan0 interface
                try:
                        # TODO 	This step define on which interface (and so IP address) the TCZ will listen
			#	to. Should not be hardcoded but should be part of the JSON configuration
			self.myIp = get_ip_address(self.interface)
			#self.myIp = 0
			print "MyIP address: " + str(self.myIp)
                except IOError:
                        self.myIp = 0
                        print "\t[WARNING] 'wlan0' interface not available"
			print "not possible to get local IP address for master filter."
                        pass

	# TODO 	LOW PRIO Theoretically we can make it more clean by filtering only the packet
	#	from the TCP stream we are interested in, after completing 3-way handshake, we can
	#	add to the filter the source and destination TCP port.
	#	On the other side, we might want to have the TCZ being able to handle more 
	#	TCP connection in parallel. DESIGN THOUGHT
	def master_filter(self, pkt):
		
		# If I could retrieve my ip address, I use it in master filter, otherwise I do not use it.
		if self.myIp == 0:
			# print "myIp is not defined"
			return 	( IP in pkt and TCP in pkt \
				and pkt[TCP].dport == self.sport \
				)
		else:
		# print "myIp is defined"
			return 	( IP in pkt and TCP in pkt \
					and pkt[IP].dst == self.myIp \
					and pkt[TCP].dport == self.sport \
			)

	# Definition of the method to access the recv buffer
	# this is intented to be called by the httz component
	def receive(self):
		# TODO	Need to work on this: if we put here the call to
		#	Queue.get(), than we have the blocking behavior inside
		#	TCZ, and we do not want this. For the moment do nothing
		#	as anyway we are calling Queue.get() from HTTZee
		
		return self.recv

	# Definition of the method to check the content of the recv buffer without
	# consuming it. I should refer to the system socket implementation to check
	# the proper naming. This does not relly have an equivalent in SOCK_STREAM
	# C socket programming
	def read(self):
		# TODO	Same as for receive()
		return self.recv

	# Definition of the operation to let external component httz write in 
	# the send buffer
	def write(self, data):
		self.toSend = data
		# There is a send_response action binded to the ESTABLISHED state
		# that should be re-used here. I'll do later TODO NEXT!
		# we can just copy that code here or in the next method send()
		
	# but a simple method that should be explicitly called
        # for example by the external httz component

	# @ATMT.action(receive_pshAck)
	def send_response(self):
	# Not sure if it makes much sense to have a method to just send, without being clear what is sent
	# but theoretically we should reach this point only via the receive_pshAck condition (and if the flag 
	# 'responseReady' is set)

		if self.toSend.__len__() > 0:
			self.l3[TCP].payload = self.toSend
			self.toSend = "" 
			# Setting the flag is part of the preparation task
			# self.l3[TCP].flags = 'A'
			
			# Handling of ACK and SEQ numbers
			# self.l3[TCP].seq = self.curSeq
			# self.l3[TCP].ack = self.curAck

                        # BD:28-09-16 Issue#16 - fetching appropriate curSeq and curAck 
                        # from cache based on the dport in packet.
                        self.l3[TCP].seq = self.curSeqHash[self.l3[TCP].dport]
                        self.l3[TCP].ack = self.curAckHash[self.l3[TCP].dport]

			self.last_packet = self.l3
			self.send(self.last_packet)
			self.last_packet[TCP].payload = None
			# TODO  Here I am 'hardcoding' the update of the local SEQ number,
			#	after sending the response.
			#       When I am using nc as client, after sending the request,
			#	a FIN-ACK is immediately send
			#       and the ACK value here is still 1 (because response form TCZee
			#	is not received yet).
			#       So TCZee get a FIN-ACK that does not ACK the HTTP Response.
			#       At this point, the send_finAck is triggered and TCZee
			#	sends the FIN-ACK to close the connection
			#       but the TCZee SEQ number is wrong as it does not consider the
			#	ACKed response from client.
			#       I believe that also in case of a client that does not
			#	immediately send the FIN-ACK without ACKing
			#       the response, the correct value should be copied from pkt. Let's see. 

			#self.l3[TCP].seq += len(self.last_packet[TCP].payload)
			#self.l3[TCP].payload = ""

	# This is a tool method used to recognized if 'pkt'
	# is a retransmitted packet or not.
	# This will be useful when we will implement different retransmission policies
	# for the moment we use to avoid increasing self.ack when we received a retransmitted packet
	def isRetransmit(self, pkt):

		if(Padding in pkt):
			pkt[Padding] = None
		if(Padding in self.lastReceived):
			self.lastReceived[Padding] = None
		
		if (self.lastReceived == ""):
			return False
		else:
			if( 	
				(self.lastReceived[TCP].ack == pkt[TCP].ack) and \
				(self.lastReceived[TCP].seq == pkt[TCP].seq) and \
				(self.lastReceived[TCP].payload == pkt[TCP].payload)
			):
				#print 	"\n\t[isRetr] lastReceived ack: " + str(self.lastReceived[TCP].ack) +\
				#	", seq: " + str(self.lastReceived[TCP].seq) +\
				#	", payload: \"" + str( self.lastReceived[TCP].payload ) + "\"" 
			 	#print   "\t[isRetr] pkt ack: " + str(pkt[TCP].ack) +\
                                #        ", seq: " + str(pkt[TCP].seq) +\
                                #        ", payload: \"" + str( pkt[TCP].payload ) + "\"\n"
				return True
			else:
				return False
		

	# Prepare the internal l3 packet before sending it
	# based on received packet
	def preparePkt(self, pkt, flag = 'A'):
		if(TCP in pkt):

                        # We are assuming this opertion is always called on 
                        # a reception of a packet. There might be a better
                        # place for this operation :)
                        #
                        # NOTE  marking STATEs as INTERCEPTED looks an interesting
                        #       point, but I can only see how to do that from the 
                        #       interctive console with t.STATE.intercepts() and not
                        #       within the definition

                        # TODO  There might be a problem in case of re-transmitted
                        #       packets and self.curAck get incremented by 1 everytime
                        #       a re-transmitted packet is received, and this is not 
                        #       the expected behavior.
			
			# print "\n\tCurrent value for local ACK: " + str( self.curAck ) + "\n"
			
			self.l3[IP].dst = pkt[IP].src
			self.dport = pkt[TCP].sport
			self.l3[TCP].dport = self.dport 
			self.l3[TCP].sport = pkt[TCP].dport

                        # BD:28-09-16 Issue#16 - fetching the curAck, curSeq from cache.
                        self.curSeq = self.curSeqHash[self.dport]
                        self.curAck = self.curAckHash[self.dport]

			if((self.curSeq + self.curAck) == 0):
				self.curAck = pkt[TCP].seq + 1
				self.curSeq = 31331
			else:
				# To avoid increasing the ACK for re-transmitted packets
				if( not self.isRetransmit(pkt) ):
					# print "\n\tPacket is no retransmitted\n"
					if (Padding in pkt):
						# Sometime (I think only in case a slow transmission is detected)
						# for small payload ( lss than 4 byte) a null Padding is added.
						# This might be due to the eth HW or TCZ stack, in any case we need
						# to remove it to avoid miscalculation with the ACK number
						pkt[Padding] = None
						# print "\n\tThere is Padding in this packet, so we remove it."

					self.curAck += pkt[TCP].payload.__len__()
					#print "\n\tTempDebug: pkt is different from self.lastReceived: \n\t" + \
					#self.lastReceived.summary() + "\n\t" + \
					#pkt.summary() + "\n\tpkt[TCP].payload.__len__(): " + \
					#str( pkt[TCP].payload.__len__() ) + "\n\tpkt[TCP].payload: \"" + \
					#str( pkt[TCP].payload ) + "\"\n\tself.curAck: " + \
					#str(self.curAck) + "\n\t" + " just added " + str(pkt[TCP].payload.__len__()) + "to it.\n"
				#else:
					#print "\n\tThis is a re-transmitted packet.\n"
					# pass

			if(pkt[TCP].ack > self.curSeq):
				self.curSeq = pkt[TCP].ack
                                
			self.l3[TCP].seq = self.curSeq
			self.l3[TCP].ack = self.curAck

                        # BD:28-09-16 Issue#16 - storing the new curAck, curSeq to cache.
                        self.curSeqHash[self.dport] = self.curSeq
                        self.curAckHash[self.dport] = self.curAck

			self.lastReceived = pkt.copy()

	# BEGIN
	@ATMT.state(initial=1)
	def BEGIN(self):
		self.l3 = IP()/TCP()
		#self.lastHttpRequest = ""
		raise  self.LISTEN()
	
	# LISTEN
	@ATMT.state()
	def LISTEN(self):
		pass

	@ATMT.receive_condition(LISTEN)
	def receive_syn(self, pkt):
		# Checking if what I got is a SYN
		if (TCP in pkt and (pkt[TCP].flags == 0x02)):
                        # BD:28-09-16 Issue#16
                        # Adding client port as key to dictionary
                        self.curAckHash[pkt[TCP].sport]=0
                        self.curSeqHash[pkt[TCP].sport]=0

			self.preparePkt(pkt)
			raise self.SYNACK_SENT()

	@ATMT.action(receive_syn)
	def send_synack(self):
		self.l3[TCP].flags = 'SA'
		self.last_packet = self.l3
		if self.jsonConfig != {} and self.jsonConfig['category']=='time' and self.jsonConfig['state']=='LISTEN':
			# This is added only for debug purposes
			print "Sleep for state %s, category %s, parameter %d"%(self.jsonConfig['category'],
									       self.jsonConfig['state'],
									        self.jsonConfig['parameter'])
			time.sleep(self.jsonConfig['parameter'])


		# Temp workaround: RPi 3 give a problem with the integrated WiFi module, packet is not 
		#	sent because size is less than 50 B, so I am adding a Padding until I learn how
		#	to properly fix the RPi issue. 
		#	NOTE:	Should be possible to avoid the problem also by using an external WiFi dongle.
		#
		#	UPDATE:	Removed the workaround, the problem was solved by running 
		#		sudo rpi-update
		#	If I understood correct, this updated the Kernel to 4.4, solving the problme with the 
		#	integrated WiFi driver.
		
		# self.last_packet.padding = "0000000000000"		

                self.send(self.last_packet)


	# SYNACK_SENT
	@ATMT.state()
	def SYNACK_SENT(self):
		pass

	@ATMT.receive_condition(SYNACK_SENT)
	def receive_ackForSyn(self, pkt):
		
		# Check if I get an ACK (0x10)
		# TODO 	A check on received pkt ACK and SEQ number would make sense,
		#	to avoid any ACK to trigger this 
		# 	condition
		# -->	For the moment I add a check on the pkt source port, so basically
		#	I am making the engine handling 1 TCP STREAM
		#	per time, that is not necessarly a bad think.
		#	This will avoid also that re-transmitted packet from other stream
		#	to mess-up the status of the server

		if TCP in pkt and (pkt[TCP].sport == self.dport) and (pkt[TCP].flags & 0x10):
			self.preparePkt(pkt)
			
			raise self.ESTABLISHED()

	# Timeout: if I do not receive the ACK after 60 seconds sending the SYN ACK, then I go back to LISTEN
	@ATMT.timeout(SYNACK_SENT, 4)
	def timeoutSynAckSent(self): 
		# We sent the SYN ACK but not received any ACK yet, timer expired --> back to LISTEN"
		self.curAck = 0
		self.curSeq = 0

                #TODO: BD:28-09-16 Issue#16 - delete the unnecessary keys to keep the cache small.
                
		raise self.LISTEN()


	@ATMT.state()
	def ESTABLISHED(self):
		pass

	# Let's try to separate all these cases in separate conditions, 
	# code should look better and TCZee.graph() would return a meaningful state chart diagram

	# in ESTABLISHED recv() FIN/ACK
	@ATMT.receive_condition(ESTABLISHED)
	def receive_finAck(self, pkt):
		# Check if the packet we got is a FIN/ACK 
		# TODO 	Make sure that in case of passive close we 
		# 	are expecting a FIN/ACK
		# TODO 	It seems like if we make the & on 0x11, and ACK is enough to make it pass
		# 	so we try to separate the checks on each flags. Check if this is true.
		#	One issue: it seems like the last ACK from the 3-way HS is somehow
		#	considered here also while running, even if I would expect this to
		#	already be consumed at this point in time
		
		if TCP in pkt and (pkt[TCP].sport == self.dport) and (pkt[TCP].flags == 0x11):
			# TODO 	here we will put the transition to the state CLOSING 
			# 	and the related action(CLOSING) will send the FIN/ACK and 
			#	keep track of the sequence and ack numbers correctly. Check 
			# 	also TCP state diagram
			
			# DEBUG
			# Adjusting the seq and ack, in case of handshake and closing, there is an
			# 
			# To consider the case detailed in the comment of the send_response,
			# I assign to the local SEQ the pkt[TCP].ack only if it is strictly 
			# bigger than the current SEQ value.
			self.preparePkt(pkt)
			raise self.CLOSING()

	# The action before transition to CLOSING is the send of FIN/ACK, that was before 
	# part of the receive_finAck condition

	@ATMT.action(receive_finAck)
	def send_finAck(self):
		self.l3[TCP].flags = 'FA'

		# Usually we arrange seq and ack in the preparPkt() method,
		# but in case of sending a SYN ACK as response to an active
		# disconnection from the client, we need to add +1 to the ack
		# even if the pkt[TCP].load.))len__() == 0                
		
		self.l3[TCP].ack += 1
		self.last_packet = self.l3
		if self.jsonConfig != {} and self.jsonConfig['category']=='time' and self.jsonConfig['state']=='ESTABLISHED':
			# This is added only for debug purposes
			print "Sleep for state %s, category %s, parameter %d"%(self.jsonConfig['category'],
									       self.jsonConfig['state'],
									       self.jsonConfig['parameter'])
			time.sleep(self.jsonConfig['parameter'])
                self.send(self.last_packet)

	
	# Second condition based on split of ESTABLISHED receive data cases
	# in ESTABLISHED recv() PSH/ACK
	@ATMT.receive_condition(ESTABLISHED)
	def receive_pshAck(self, pkt):

		# check if the received packet is a PSH/ACK 0x18
		# TODO 	EPIC this will need to consider also the case of HTTP requests splitted over
		#	multiple TCP segments, for the moment we assume request fits in one segment.
		#
		#	NOTES: 	HTTP Request can be
		#
		#		- Without a body: The request is completed when 
		#		  you have 2 consecutives new lines
		#		  0x0A 0x0D 0x0A 0x0D (but we should gracefully consider also LR only			
		#
		#		- With a body: In this case, the request terminate
		#			- when the number of char indicated in Content-length is reached
		#			- according to the logic to handle the Chunked request
		#
		 
		# TODO 	Assuming that the HTTP data will be always contained in a TCP segment flagged as
		# httz	PSH/ACK, this is not necessarly true. In general all the data that arrives
		#	should be copied in the recv buffer
		
		if TCP in pkt and (pkt[TCP].sport == self.dport) and (pkt[TCP].flags == 0x18):
			
			# TODO 	As of now, we are just assuming that the content of the TCP load
			#	is an HTTP request, this might be also something else in a more advanced version
			#	but if we need to start from somewhere, that's for sure HTTP(S)
			
			# TODO	Adding here a check to verify if we are already processing the request just
			#	received. Maybe we can go to another state (something like PROCESSING_REQUEST)
			# 	to avoid that retransmission from the client mess-up the ACK counting. We clean 
			# 	this buffer when timeout, because I might want to make 2 consecutive requests for
			#	the same resource.

			if pkt[TCP].load : #and (pkt[TCP].load != self.lastHttpRequest) : 
		
				# Adding the received load to the recv buffer
				self.recv.put( str( pkt[TCP].load ) )

				# We consume the content of the TCP load
				# by printing it, until we have an HTTZee to do something
				# more meaningful with it
				#print "\n[TCP Payload] " + self.receive() 
				#print "\n"

				self.preparePkt(pkt)
	
			# If received pkt has no load OR if the HTTP request is already received
			# in this case I do nothing
			# self.l3[TCP].seq = pkt[TCP].ack
			
			# Still in the assumption that whatever PSH/ACK TCP packet we receive from the client
			# will actually contains an HTTP request. Also, I am assuming that all the sizes goes 
			# automatically with Scapy magic
			# TODO seems like sending the ACK for the request and the response in the same TCP segment
			# is not ok, trying to send them separatelly
			# self.l3[TCP] = httpResponse
			
			# ??? 	it is still not clear what is better in such a situation: put here the send() call
			# 	or put it in the action related to this state? Question arises because based on
			# 	content of the pkt I might need different actions triggered, 
			#	without the change of state.
			#	Does this even make sense?
			#	I send here for the moment as I need to send the ACK but 
			#	I do not need to change the state.
			#	This is different to the previous if case, for example,
			#	where also the state change.
			#
			# !!!	For the moment the best answer to this is that we should
			#	have a different ATMT.receive_condition 
			#	for each case of the if, and send the response packet in
			#	the action of each condition.
			#	From code execution point of view maybe no difference in
			#	the 2 approaches, but thi separation
			#	allow to generate automatically a much more clear state diagram with TCZee.graph()

                	# self.l3 = self.l3/httpResponse
			# self.responseReady = 1
			# Just want to move the send() call into the related ATMT.action, just to keep 
			# the code clean and according to state machine formalism

				raise self.ESTABLISHED()

	@ATMT.action(receive_pshAck)
	def sendAck(self):
		self.l3[TCP].flags = 'A'
		self.last_packet = self.l3
		if self.jsonConfig != {} and self.jsonConfig['category']=='time' and self.jsonConfig['state']=='ESTABLISHED':
			# This is added only for debug purposes
			print "Sleep for state %s, category %s, parameter %d"%(self.jsonConfig['category'],
									       self.jsonConfig['state'],
									       self.jsonConfig['parameter'])
			time.sleep(self.jsonConfig['parameter'])
		self.send(self.last_packet)

	# in ESTABLISHED recv() a SYN (basically client want to start a new tcp stream)
	@ATMT.receive_condition(ESTABLISHED)	
	def receive_synInEstablished(self, pkt):
		# For this receive condition I do not check the source port, because if I get a SYN
		# while in ESTABLISHED, it might be the client trying to open a new tcp strem
		# TODO 	Check if in this multi tcp stream handling approach is correct or if we should
		#	simply put a timer for the ESTABLISHED state and let the state
		#	machine going back to LISTEN after sending the response
		#	We should check the "Keep Alive" header...

		if TCP in pkt and (pkt[TCP].flags == 0x02) :
			self.preparePkt(pkt)
			self.l3[TCP].seq = 0
			self.l3[TCP].ack = pkt[TCP].seq + 1

			# We have a new TCP stream!
			self.l3[TCP].dport = pkt[TCP].sport
			self.dport = pkt[TCP].sport

			self.l3[TCP].payload = ""
			raise self.SYNACK_SENT()

	@ATMT.action(receive_synInEstablished)
	def sendSyn_inEstablished(self):
      		self.l3[TCP].flags = 'SA'
                self.last_packet = self.l3
                if self.jsonConfig != {} and self.jsonConfig['category']=='time' and self.jsonConfig['state']=='ESTABLISHED':
			# This is added only for debug purposes
			print "Sleep for state %s, category %s, parameter %d"%(self.jsonConfig['category'],
									       self.jsonConfig['state'],
									       self.jsonConfig['parameter'])
			time.sleep(self.jsonConfig['parameter'])
                self.send(self.last_packet)
	
	@ATMT.receive_condition(ESTABLISHED)
	def receive_ackInEstablished(self, pkt):
		if TCP in pkt and (0x10 == pkt[TCP].flags):
			self.preparePkt(pkt)
			raise self.ESTABLISHED()
		else:
			pass

	@ATMT.state() # Final just for the moment to avoid the warning
	def CLOSING(self):
		#DEBUG 
		#print "[DEBUG] entering [CLOSING]"
		print ""
			
	@ATMT.receive_condition(CLOSING)
	def receive_ack_closing(self, pkt):
		# Instead of going back to LISTEN I go to the final state to have an exit condition
		# for the state machine
		# raise self.LISTEN()

		if (TCP in pkt and (pkt[TCP].flags == 0x10)):
			raise self.END()
			# print ""
			# NOTE:	Go again back to LISTEN, in order to be able to handle several request with the same
			#	instance of TCZ/HTTZ. If a client sends a request and close the connection when te response
			#	is received (for example, because of 'Connection: close' header), this will terminate the 
			#	main script, so a second request will not find anything listening for it.
		#else:
		#	# something else received
		#	# DEBUG
		#	print "\t\t[DEBUG][CLOSING] We receive something that is not an ACK: " + pkt.summary()
		#	pass
	# After timeout in CLOSING, terminate (basically only one FIN from
	# the client is enough to close connection
	# TODO	THIS IS WRONG!
	@ATMT.timeout(CLOSING, 5)
	def timeoutClosing(self):
		self.l3[TCP].ack = 0
                self.l3[TCP].seq = 0
                self.l3[TCP].payload = ""
                self.last_packet = self.l3
                raise self.LISTEN()

	# This is simply a final state to have an exit condition
	# once the TCP terminate connection is completed
	@ATMT.state(final=1)
	def END(self):
		raise self.BEGIN()

class HTTZee(object):

	def __init__(self, tcz):
		# Threading stuff
		
		# Prepare a separate thread for the TCZee run
		httzThread = Thread(target=self.run)
		httzThread.daemon = True
		

		tczThread = Thread(target=self.connection)
		# tczThread.daemon = True

		# Adding a reference to the TCZ used as TCP stack
		self.tcz = tcz
                self.lock = threading.Lock()
		self.resources = {}
		

		body = "Example of Content category TestCase content."
		bodySize = body.__len__()

		if( tcz.jsonConfig != {} and tcz.jsonConfig['resources'] != "" ):

			for res in self.tcz.jsonConfig['resources']:
	
				bodySize = res['body'].__len__()

				# NOTE:	We need to dinamically calculate the size of body and add the Content-length header.
				# TODO:	For the moment we assume that this header is not in the JSON file, we might
				#	add a mechanism to check if the header is presentinthe JSON and replace it with the 
				#	dinamically calculated value.
				#	Check re module for regular expression (str.replace() does not understand regex)
				headers = res['headers']
				headers = headers.rstrip()
				headers += "\r\nContent-length: " + str(bodySize) + "\r\n\r\n"
				
				self.resources[res['resource']] = str(headers + res['body'])

		else:
			print "[ERROR] HTTZee initialized without correct JSON config file. No resources available."
			exit() 


		tczThread.start()
		httzThread.start()

	
	def connection(self):
		print "\t[HTTZ][connection()] Starting TCZee thread"
		self.tcz.run()

	def run(self):
		s = ""
		print "\t[HTTZ][run()] called TCZee.run(), entering infinite loop now."
		while ( s != "exit" ):
			# We will need a call to recv() instead of directly
			# accessing the TCZ Queue, but for the moment this is
			# fine. This is a blocking call.
                        self.lock.acquire()
                        print 'lock acquired by %s' %threading.current_thread().name
			s = str( self.tcz.recv.get() )
			print "\t[HTTZ][run()] Received data: " + s + "\n"
			self.processRequest(s)
                        print 'lock released by %s' % threading.current_thread().name
                        self.lock.release()

		

	def processRequest(self, req):
		# TODO	Here we will need the logic to parse the whole HTTP request
		#	and return the requested resource. This include the logic to
		#	parse HTTP Header, URL parameters and body.
		#	No need to re-invent the wheel here, we can use existing libraries.
		#
		#	For the sake of the demo, we assume now req contains the whole
		#	HTTP request

		for p in req.split():
                        print "\t[HTTZ] spliting request:" + p
			if (p in self.resources.keys() ):
				print "\t[HTTZ][processRequest] Matching resource, sending response: " + self.resources[p]
				self.tcz.write(self.resources[p])
                                # Added by bdesikan on 18-Sep-16 during debug session
                                # Temporary Patch to fix the mismatch in th Ack number 
                                # due to synchronization issue between the TCZ and HTTZ components.
                                #TODO: Fix using robust approah
                                time.sleep(1)
				self.tcz.send_response()

		#return self.resources[req]

	



#TCZee.graph()
#t = TCZee(80, debug=3)
#t.run()
