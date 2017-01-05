from scapy.all import *
from common import *
from tcz import TCZee
from httz import HTTZee
from dnz import DNZee
import time
import sys
import signal
from functools import wraps
# Just a small utility to get from system the ip of a specific network interface
import socket
import fcntl
import struct
import threading
import inspect

from Queue import Queue
from threading import Thread

class Connector(Automaton):

    def jsonConfig(self, conf = {}):
        self.config = conf

        # Legacy JSON format, keep it for the moment until 
        # migration to JSON-schema is completed
        if 'listeningPort' in self.config:
            self.localPort = int( self.config['listeningPort'] )
        elif 'tcp-port' in self.config:
            self.localPort = int( self.config['tcp-port'] )
        else:
            self.localPort = 80

        if 'dns-port' in self.config:
            self.dnsPort = self.config['dns-port']
            # [MZ 03.01.2016] TODO for BD: please add here the code to configure the DNZee based 
            #                      on the content of the JSON paramters. I do not want to pass the 
            #                      full JSON to DNZee, we should have method calls to add entries to
            #                      DNZee internal list of "q-addr"/"response" pairs
            print ">>>[remove] about to check the JSON" 
            if 'configs' in self.config:
                print ">>>[remove] configs is there, about to iterate"
                for c in self.config['configs']:
                    print ">>>[remove] there is at least one item in configs"
                    # DNS category #
                    if c['category'] == 'dns':
                        dnz = DNZee(self.dnsPort, debug=3)
                        print ">>>[remove] this item is a DNS category"
                        # Parsing the "dnz-conf" object type of json-schema to avoid
                        # parsing for every look-up
                        lookupDB = c['parameters']
                        for record in lookupDB:
                            key = record['q-addr']
                            value = record['response']
                            dnz.add_dnsLookUp(key,value)
                        dnzThread = Thread(target=dnz.run, name='DNS_Thread')
                        dnzThread.daemon = True

                        # Starting the TCZ Threads
                        dnzThread.start()     
                        
        # Legacy JSON format, keep it for the moment until 
        # migration to JSON-schema is completed
        if 'listeningInterface' in self.config:
            self.interface = str( self.config['listeningInterface'] )
        # This is the new and correct JSON value to expect
        elif 'interface' in self.config:
            self.interface = str( self.config['interface'] )
        else:
            self.interface = "eth0"


    def parse_args(self, jsonConfig={}, **kargs):
        Automaton.parse_args(self, **kargs)
        self.lastReceived = ""
        
        self.localPort = -1
        self.dnsPort = -1
       
        self.jsonConfig(jsonConfig)
 
        try:
            # TODO  This step define on which interface (and so IP address) the TCZ will listen
            #       to. Should not be hardcoded but should be part of the JSON configuration
            self.localAddr = get_ip_address(self.interface)
            #self.myIp = 0
            print "MyIP address: " + str(self.localAddr)
        except IOError:
            self.localAddr = 0
            print "\t[WARNING] '" + self.interface + "' interface not available"
            print "not possible to get local IP address for master filter."
            pass

        self.connections = []

    # check only matching incoming packets
    def master_filter(self, pkt):
        if (self.localAddr != 0):
            return  ( IP in pkt and TCP in pkt \
                    and pkt[IP].dst == self.localAddr \
                    and pkt[TCP].dport == self.localPort
                    )
        else:
            return  ( IP in pkt and TCP in pkt \
                    and pkt[TCP].dport == self.localPort
                    )
    
    # This is a tool method used to recognized if 'pkt'
    # is a retransmitted packet or not.
    # This will be useful when we will implement different retransmission policies
    # for the moment we use to avoid increasing self.ack when we received a retransmitted packet
    def isRetransmit(self, pkt):
        if (self.lastReceived == ""):
            return False
        
        if(Padding in pkt):
            pkt[Padding] = None
        if(Padding in self.lastReceived):
            self.lastReceived[Padding] = None

        else:
            if(
                (self.lastReceived[TCP].ack == pkt[TCP].ack) and \
                (self.lastReceived[TCP].seq == pkt[TCP].seq) and \
                (self.lastReceived[TCP].payload == pkt[TCP].payload)
            ):
                return True
            else:
                return False



    # BEGIN state
    @ATMT.state(initial=1)
    def CON_BEGIN(self):
        raise self.CON_LISTEN()

    @ATMT.state()
    def CON_LISTEN(self):
        pass

    @ATMT.receive_condition(CON_LISTEN)
    def con_receive_syn(self, pkt):
        
        if( 'S' in flags(pkt[TCP].flags) and not self.isRetransmit(pkt) ): 
            # create a model for TCZ, with no pkt and no configuration
            self.tcz = TCZee(pkt, {}, debug=3)
            self.tcz.confTCZ(self.localPort, self.interface)
            conf = self.config

            contentFlag = False
            
            print ">>>[remove] about to check the JSON" 
            if 'configs' in conf:
                print ">>>[remove] configs is there, about to iterate"
                for c in conf['configs']:
                    print ">>>[remove] there is at least one item in configs"
                    # TIME #
                    if c['category'] == 'time':
                        print ">>>[remove] this item is a time category"
                        # Iterate on Delay parameters
                        for p in c['parameters']:
                            print ">>>[remove] param for this time cat: " + str(p['state']) + ", " + str(p['action']) + ", " + str(p['delay']) 
                            cd = confDelay( p['state'], p['action'], p['delay'] )
                            self.tcz.addDelayConf(cd)
                    # PACKET #
                    elif c['category'] == 'packet':
                        print ">>>[remove] packet category"
                        for p in c['parameters']:
                            print ">>>[remove][packet] at least one parameter here"
                            if p['sub-category'] == 'tcz':
                                print ">>>[remove][packet] TCZ"
                                cp = confTCZ( p['state'], p['action'], p['flags'] )
                                self.tcz.addPacketConf(cp)
                            elif p['sub-category'] == 'icmz':
                                print ">>>[remove][packet] ICMZ"
                                cp = confICMZ( p['state'], p['action'], p['type'], p['code'] )
                                self.tcz.addPacketConf(cp)
                    # CONTENT #
                    elif c['category'] == 'content':
                        print ">>>[remove][content] at least one category content"
                        self.httz = HTTZee(self.tcz)
                        contentFlag = True
                        for p in c['parameters']:
                            print ">>>[remove][content] Loading resource: " + str(p['resource'])
                            self.httz.addResource(p['resource'], p['http-status'], p['headers'], p['body'])
    
            if(contentFlag):
                httzThread = Thread(target=self.httz.run, name='httz-thread')
                tczThread = Thread(target=self.httz.connection, name='httz-tcz-thread')
                httzThread.daemon = True
                httzThread.start()
                tczThread.start()
            else:
                tczThread = Thread(target=self.tcz.run, name='tcz_Thread_Packet')
                tczThread.deamon = True
                tczThread.start()
                    
        self.lastReceived = pkt
        self.connections.append(self.tcz)

        #elif self.config['category'] == 'dns':
            # DNZee component for DNS look-up from browser 
            # DNS is using UDP-only implementation for the time-being.
            #dnz = DNZee(self.config, self.localPort, debug=3)
            #dnzThread = Thread(target=dnz.run, name='DNS_Thread')
            #dnzThread.daemon = True

            # Starting the TCZ Threads
            #dnzThread.start()             

            # TODO here we create a new instance of
            # HTTZee (that contains a TCZee).
            #
            # 1. TCZee need to start from SYN_ACK sent state
            #
            # 2. TCZee master_filter should be change to accept
            #    only packet that belongs to his connection
            #
            # 3. Connector needs to keep track of current open
            #    connections and avoid create new Thread for
            #    re-transmitted packets.
            #
            # 4. When connection is closed, HTTZ Thread should die
            #    and notify Connector

        raise self.CON_LISTEN()
