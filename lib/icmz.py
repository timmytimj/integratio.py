#! /usr/bin/python

# DNZee - Scapy-based basic implementation of  ICMP component 
# for acting a compontent in Integratio
# Copyright (C) 2016 Marco Zunino

from scapy.all import *
from common import *
import time

# Just a small utility to get from system the ip of a specific network interface
import socket
import fcntl
import struct

class ICMZee(Automaton):
    def parse_args(self, jsonConfig={}, sport=53, **kargs):
        # DEBUG 
        #print "[DEBUG] Starting processing parameters" 
        Automaton.parse_args(self, **kargs)
        self.sport = sport
        self.dport = 0
        self.responseReady = 0
        self.synAckReady = 0
        self.myIp = 0
        # TODO  Keep track of last processed HTTP request, to 
        #   avoid problems with retransmission. Need to be refactored and cleaned up
        self.lastHttpRequest = ""
        self.jsonConfig=jsonConfig
        if 'listeningInterface' in self.jsonConfig:
            self.interface = str( self.jsonConfig['listeningInterface'] )
        else:
            self.interface = "wlan0"
        self.localAddr = get_ip_address(self.interface)

        
    def master_filter(self, pkt):
        return  (IP in pkt and ICMP in pkt \
                and not((TCP in pkt) or (UDP in pkt) or(DNS in pkt)) \
                and pkt[IP].dst == self.localAddr) 

    # BEGIN
    @ATMT.state(initial=1)
    def BEGIN(self):
        self.l3 = IP()/ICMP()
        raise  self.LISTEN()
    
    # LISTEN
    @ATMT.state()
    def LISTEN(self):
        pass

    @ATMT.receive_condition(LISTEN)
    def received_ICMP(self, pkt):
        if (ICMP in pkt):
            print "got icmp with custom data of expected length:", pkt[ICMP].type,pkt[ICMP].load
            self.l3[IP].src = self.localAddr
            self.l3[IP].dst = pkt[IP].src
            # self.l3[ICMP].type = 3
            # self.l3[ICMP].id = pkt[ICMP].id
            self.l3[ICMP].load = pkt[ICMP].load

            if (len(pkt[ICMP].load)<6):
                if int(self.jsonConfig['icmpResponse'], 16) == int(pkt[ICMP].load, 16):
                   self.l3[ICMP].type = 3
                   self.l3[ICMP].code = int(pkt[ICMP].load, 16)
                else:
                   self.l3[ICMP].type = 0
                   # self.l3[ICMP].code = 0
            else:
                self.l3[ICMP].type = 0
                # self.l3[ICMP].code = 0
            
            raise self.LISTEN()

    @ATMT.action(received_ICMP)
    def send_echo_response(self):
        self.send(self.l3)
        
