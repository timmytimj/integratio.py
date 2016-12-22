from scapy.all import *
from common import *
from tcz import TCZee
from httz import HTTZee
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
        # set listening port
        if 'listeningPort' in jsonConfig:
            self.localPort = int( jsonConfig['listeningPort'] )
        else:
            self.localPort = 80

        # TODO This is duplicate code, we can keep it only in the connector
        # and reference the local ip inform from the Connector in TCZee
        if 'listeningInterface' in self.config:
            self.interface = str( self.config['listeningInterface'] )
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
        self.lookupDict = {}
        self.l3_dnz = IP()/UDP()/DNS() # Packet to be used with the DNZ component 

    # check only matching incoming packets
    def master_filter(self, pkt):
        if (self.localAddr != 0):
            return  ( IP in pkt \
                    and pkt[IP].dst == self.localAddr)
        else:
            return  ( IP in pkt )

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

        if self.config['category'] == 'packet':
            # Parsing the DNz look up into a single instance varible to avoid
            # parsing for every look-up
            lookupDB = self.config['dnzLookUp']
            for record in lookupDB:
                self.lookupDict.update(record)

        raise self.CON_LISTEN()

    @ATMT.state()
    def CON_LISTEN(self):
        pass

    @ATMT.receive_condition(CON_LISTEN, prio=1)
    def tcz_receive_syn(self, pkt):

        if( IP in pkt and TCP in pkt \
            and pkt[TCP].dport == self.localPort \
            and 'S' in flags(pkt[TCP].flags) and not self.isRetransmit(pkt) ):
            # tcz = TCZee(self.config, pkt, debug=3)
            # Check impact of DEBUG messages on performances

            # BD: issue#17: For creating a dummy Httz for time category
            # cases. status_http parameter is passed to HTTZee class.
            # status_http = 0 means dummy httz component used for time.
            # status_http = 1 means proper httz component used for content.
            if self.config['category']=='time':
                # Create TCZ Object
                tcz = TCZee(self.config, pkt, debug=3)

                # Prepare only the Thread for TCZ
                # BD: removed the threading in my current testing
                tczThread = Thread(target=tcz.run, name='tcz_Thread_time')
                tczThread.daemon = True

                # Starting the TCZ Threads
                tczThread.start()

            elif self.config['category']=='content':
                # Create TCZ and HTTZ Objects
                tcz = TCZee(self.config, pkt, debug=3)
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
                # For the moment only a TCZee is needed for the
                # packet use case.
                # TODO need to mix with content use cases

                # Create TCZ and DNZ Objects
                tcz = TCZee(self.config, pkt, debug=3)

                # Prepare TCZ Thread
                tczThread = Thread(target=tcz.run, name='tcz_Thread_Packet')
                tczThread.daemon = True

                # Starting the TCZ and DNZ Threads
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
    
    @ATMT.receive_condition(CON_LISTEN, prio=0)
    def dnz_query(self, pkt):
        # Checking if what I got has a DNS layer 
        # print "Port :",pkt[UDP].dport
        if (IP in pkt and UDP in pkt \
           and pkt[UDP].dport == 53 \
           and pkt[IP].dport == 53 \
           and self.config['category'] == 'packet'):
            self.l3_dnz[IP].dst = pkt[IP].src
            self.l3_dnz[IP].src = pkt[IP].dst
            self.l3_dnz[IP].id  = pkt[IP].id
            self.l3_dnz[UDP].dport = pkt[UDP].sport
            self.l3_dnz[UDP].sport = 53
            self.l3_dnz[DNS].id = pkt[DNS].id
            self.l3_dnz[DNS].aa = 1
            self.l3_dnz[DNS].qr = 1
            self.l3_dnz[DNS].rd = pkt[DNS].rd
            self.l3_dnz[DNS].qdcount = pkt[DNS].qdcount
            self.l3_dnz[DNS].qd = pkt[DNS].qd

            if(self.lookupDict.has_key(pkt[DNS].qd.qname[:-1])) :
                self.l3_dnz[DNS].ancount = 1
                self.l3_dnz[DNS].an = DNSRR(rrname=self.l3_dnz[DNS].qd.qname, type='A', ttl=3600, rdata=self.lookupDict[pkt[DNS].qd.qname[:-1]] )
            else:
                self.l3_dnz[DNS].ancount = 0
                self.l3_dnz[DNS].an = None
                self.l3_dnz[DNS].rcode = "name-error"
            raise self.CON_LISTEN()

    @ATMT.action(dnz_query)
    def send_answer(self):
        self.send(self.l3_dnz)	
