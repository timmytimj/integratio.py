#! /usr/bin/python

# DNZee - Scapy-based basic implementation of DNS component using UDP
# for acting a compontent in Integratio
# Copyright (C) 2016 Marco Zunino

from scapy.all import *
from common import *
from scapy.layers.dns import DNSRR, DNS, DNSQR
import time

# Just a small utility to get from system the ip of a specific network interface
import socket
import fcntl
import struct

class DNZee(Automaton):
    def parse_args(self, jsonConfig={}, sport=53, **kargs):
        # DEBUG 
        #print "[DEBUG] Starting processing parameters" 
        Automaton.parse_args(self, **kargs)
        self.sport = sport
        self.dport = 0
        self.responseReady = 0
        self.synAckReady = 0
        self.myIp = 0
        self.lookupDict = {}

	# Parsing the DNz look up into a single instance varible to avoid
        # parsing for every look-up
        lookupDB = jsonConfig['dnzLookUp']
        for record in lookupDB:
            self.lookupDict.update(record)   

        # TODO  Keep track of last processed HTTP request, to 
        #   avoid problems with retransmission. Need to be refactored and cleaned up
        self.lastHttpRequest = ""
        self.jsonConfig=jsonConfig
        
    def master_filter(self, pkt):
        return  ( IP in pkt and UDP in pkt \
            and pkt[UDP].dport == self.sport \
            )

    # BEGIN
    @ATMT.state(initial=1)
    def DNZ_BEGIN(self):
        self.l3 = IP()/UDP()/DNS()
        #self.lastHttpRequest = ""
        raise  self.DNZ_LISTEN()
    
    # LISTEN
    @ATMT.state()
    def DNZ_LISTEN(self):
        pass

    @ATMT.receive_condition(DNZ_LISTEN)
    def check_query(self, pkt):
        # Checking if what I got has a DNS layer 
        # print "Port :",pkt[UDP].dport
        if pkt[IP].dport == 53:
            self.l3[IP].dst = pkt[IP].src
            self.l3[IP].src = pkt[IP].dst
            self.l3[IP].id  = pkt[IP].id
            self.l3[UDP].dport = pkt[UDP].sport
            self.l3[UDP].sport = 53
            self.l3[DNS].id = pkt[DNS].id
            self.l3[DNS].aa = 1
            self.l3[DNS].qr = 1
            self.l3[DNS].rd = pkt[DNS].rd
            self.l3[DNS].qdcount = pkt[DNS].qdcount
            self.l3[DNS].qd = pkt[DNS].qd
            
            if(self.lookupDict.has_key(pkt[DNS].qd.qname[:-1])) :
                self.l3[DNS].ancount = 1
                self.l3[DNS].an = DNSRR(rrname=self.l3[DNS].qd.qname, type='A', ttl=3600, rdata=self.lookupDict[pkt[DNS].qd.qname[:-1]] )
            else:
                self.l3[DNS].ancount = 0
                self.l3[DNS].an = None
                self.l3[DNS].rcode = "name-error"
        raise self.DNZ_LISTEN()

    @ATMT.action(check_query)
    def send_answer(self):
        self.send(self.l3)
        
