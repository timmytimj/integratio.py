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

    def parse_args(self, jsonConfig={}, **kargs):
        Automaton.parse_args(self, **kargs)
        self.config = jsonConfig
        self.lastReceived = ""
        
        # Legacy JSON format, keep it for the moment until 
        # migration to JSON-schema is completed
        if 'listeningPort' in self.config:
            self.localPort = int( self.config['listeningPort'] )
        elif 'lis-port' in self.config:
            self.localPort = int( self.config['lis-port'] )
        else:
            self.localPort = 80

        # Legacy JSON format, keep it for the moment until 
        # migration to JSON-schema is completed
        if 'listeningInterface' in self.config:
            self.interface = str( self.config['listeningInterface'] )
        # This is the new and correct JSON value to expect
        elif 'interface' in self.config:
            self.interface = str( self.config['interface'] )
        else:
            self.interface = "wlan0"

        # We are assuming here that IntegratioWebServer is listening on wlan0 interface
        try:
            # TODO  This step define on which interface (and so IP address) the TCZ will listen
            #       to. Should not be hardcoded but should be part of the JSON configuration
            self.localAddr = get_ip_address(self.interface)
            #self.myIp = 0
            print "MyIP address: " + str(self.localAddr)
        except IOError:
            self.localAddr = 0
            print "\t[WARNING] 'wlan0' interface not available"
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
        # DNZee component for DNS look-up from browser 
        # DNS is using UDP-only implementation for the time-being.
        raise self.CON_LISTEN()

    @ATMT.state()
    def CON_LISTEN(self):
        pass

    @ATMT.receive_condition(CON_LISTEN)
    def con_receive_syn(self, pkt):
        
        if( 'S' in flags(pkt[TCP].flags) and not self.isRetransmit(pkt) ):
            # tcz = TCZee(self.config, pkt, debug=3)
            # Check impact of DEBUG messages on performances

            # BD: issue#17: For creating a dummy Httz for time category
            # cases. status_http parameter is passed to HTTZee class.
            # status_http = 0 means dummy httz component used for time.
            # status_http = 1 means proper httz component used for content.
            if self.config['category']=='time':
                # MZ 26.12.2016 JSON is used again, but in a separate TCZee method TCZee.jsonConf()
                # This method works with JSON-schema defined JSON config
                tcz = TCZee(pkt, self.config, debug=3)

                # BD: removed the threading in my current testing
                tczThread = Thread(target=tcz.run, name='tcz_Thread_time')
                tczThread.daemon = True

                # Starting the TCZ Threads
                tczThread.start()

            elif self.config['category']=='content':
                # Create TCZ and HTTZ Objects
                tcz = TCZee(pkt, self.config, debug=3)
                httz = HTTZee(tcz)

                # Prepare HTTZ Thread
                httzThread = Thread(target=httz.run, name='httz_Thread_Content')
                httzThread.daemon = True

                # Prepare a separate thread for the TCZee run
                tczThread = Thread(target=httz.connection, name='tcz_Thread_Content')

                # Starting the respective Threads
                tczThread.start()
                httzThread.start()

            elif self.config['category'] == 'packet':
                # MZ 26.12.2016 Same as for the time category above
                # NOTE  We still pass JSON configuration from Connector to TCZ, but the TCZee.jsonConf() 
                # method is now able to distinguish between 'packet' and 'delay' configuration, so the code here
                # and at line 122 can be the same.
                # Before consolidate 'time' and 'packet' in a single 'if branch', we need to discuss how DNS use
                # cases fit in this logic.
                tcz = TCZee( pkt, self.config, debug=3)

                tczThread = Thread(target=tcz.run, name='tcz_Thread_Packet')
                tczThread.deamon = True
                tczThread.start()
                
            self.lastReceived = pkt
            self.connections.append(tcz)
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
