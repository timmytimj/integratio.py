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
#   iptables -A OUTPUT -p tcp --tcp-flags RST RST -j DROP
#
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
import inspect

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

# return a list of flag 'chars' given an int
# (p[TCP].flags)
def flags(p):
    flagSeq = ['F', 'S', 'R', 'P', 'A', 'U', 'E', 'C']
    f = []
    c = 1

    for i in range(0,8):
        if(p & c):
            f.append(flagSeq[i])
        c = c << 1
    return f

# Tool method to return a lsit of chunk, given
# a string and the size of chunk.
# The last chunk might be smaller than chunk size.
def chunkstring(string, length):
    return list((string[0+i:length+i] for i in range(0, len(string), length)))

class TCZee(Automaton):
    def parse_args(self, jsonConfig={}, pkt = IP(), **kargs):
        # DEBUG
        #print "[DEBUG] Starting processing parameters"
        Automaton.parse_args(self, **kargs)
        self.initSYN = pkt
        if 'listeningPort' in jsonConfig:
            self.localPort = int( jsonConfig['listeningPort'] )
        else:
            self.localPort = 80

        self.remotePort = self.initSYN[TCP].sport
        self.remoteAddr = self.initSYN[IP].src

        # For some reason, self.l3 is not available at this point in time
        #self.l3[TCP].sport = self.initSYN[TCP].dport
        #self.l3[TCP].dport = self.initSYN[TCP].sport

        self.curAck = 0
        self.curSeq = 0

        # recv and send buffer to be used by the external     httz component
        self.recv = Queue()
        self.toSend = ""
        self.jsonConfig=jsonConfig

        # Keeping track of the last valid packet received
        self.lastReceived = ""

        if 'listeningInterface' in self.jsonConfig:
            self.interface = str( self.jsonConfig['listeningInterface'] )
        else:
            self.interface = "wlan0"

        # We are assuming here that IntegratioWebServer is listening on wlan0 interface
        try:
            # TODO  This step define on which interface (and so IP address) the TCZ will listen
            #   to. Should not be hardcoded but should be part of the JSON configuration
            self.localAddr = get_ip_address(self.interface)
            #self.myIp = 0
            print "MyIP address: " + str(self.localAddr)
        except IOError:
            self.localAddr = 0
            print "\t[WARNING] 'wlan0' interface not available"
            print "not possible to get local IP address for master filter."
            pass

    # With new architecture, we are handling now multiple TCP connection,
    # but only 1 per TCZee instance. So the master filter should only
    # get the TCP packets from this stream.
    def master_filter(self, pkt):
        if self.localAddr == 0:
            # print "myIp is not defined"
            return  ( IP in pkt and TCP in pkt \
                and pkt[TCP].dport == self.localPort \
                        and pkt[TCP].sport == self.remotePort
                )
        else:
            return  ( IP in pkt and TCP in pkt \
                and pkt[IP].dst == self.localAddr \
                and pkt[TCP].dport == self.localPort \
                        and pkt[TCP].sport == self.remotePort
                )

    # Definition of the method to access the recv buffer
    # this is intented to be called by the httz component
    def receive(self):
        # TODO  Need to work on this: if we put here the call to
        #   Queue.get(), than we have the blocking behavior inside
        #   TCZ, and we do not want this. For the moment do nothing
        #   as anyway we are calling Queue.get() from HTTZee

        return self.recv

    # Definition of the method to check the content of the recv buffer without
    # consuming it. I should refer to the system socket implementation to check
    # the proper naming. This does not relly have an equivalent in SOCK_STREAM
    # C socket programming
    def read(self):
        # TODO  Same as for receive()
        return self.recv

    # Definition of the operation to let external component httz write in
    # the send buffer
    def write(self, data):
        self.toSend = data

    # but a simple method that should be explicitly called
        # for example by the external httz component
    

    # [feature/action-override] Trying to override send method to check
    # for current action and include the time delay

    # MZ 13.11.2016 Created branch to support packet category
    # from feature/action-override as base
    def send(self, pkt):
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 1)
        print "\t\t[NEW DEBUG] Caller frame: ", calframe[1][3]+ "-- current Thread --" + (threading.current_thread().name) + ", ID -- "+ str(threading.current_thread().ident)+"\n"

        ''' BD: Commented my commmit code as its only a refernce during  discussions.'''

        if self.jsonConfig != {} and self.jsonConfig['category']=='time' and self.jsonConfig['state']==self.state.state and self.jsonConfig['action'] == calframe[1][3]:
            # This is added only for debug purposes
            print "Sleep for state %s, category %s, parameter %d -- current Thread -- %s"%(self.jsonConfig['category'],
                                           self.jsonConfig['state'],
                                            self.jsonConfig['parameter'], threading.current_thread().name)
            time.sleep(self.jsonConfig['parameter'])
        # This is a nice place also for specific packet response, 
        # not only for time category
        if 'category' in self.jsonConfig and self.jsonConfig['category'] == 'packet':
            if 'state' in self.jsonConfig and self.jsonConfig['state'] == calframe[1][3]:
                if 'parameter' in self.jsonConfig:
                    #pkt[TCP].flags = self.jsonConfig['parameter']
                    pkt[TCP].flags = 'R'
                    print "\t\t[NEW DEBUG] Here we should have the packet handling test case -- current Thread --%s, ID -- %d"%(threading.current_thread().name, threading.current_thread().ident)
                    print pkt.summary()

        super(TCZee, self).send(pkt)




    # @ATMT.action(receive_pshAck)
    def send_response(self):
        if self.toSend.__len__() == 0:
            # nothing to send, pass over
            pass
        else:
            self.l3[TCP].flags = 'A'
            # If we want to send less than 1024 B, we do that in a single packet
            if self.toSend.__len__() < 1024: 
                self.l3[TCP].payload = self.toSend
                self.toSend = ""

                # TODO  There can be different approach to send_response, in case of 
                #       payload > 1500 (multiple packets). For example:
                #
                #           1.  Sending all the packets in a row
                #           
                #           2.  Sending the first 1024 bytes, wait for ACK and then proceed 
                #               with the rest
                #
                #


                # Handling of ACK and SEQ numbers
                self.l3[TCP].seq = self.curSeq
                self.l3[TCP].ack = self.curAck

                self.last_packet = self.l3
                self.send(self.last_packet)
                self.last_packet[TCP].payload = None
                # TODO  Here I am 'hardcoding' the update of the local SEQ number,
                #   after sending the response.
                #       When I am using nc as client, after sending the request,
                #   a FIN-ACK is immediately send
                #       and the ACK value here is still 1 (because response form TCZee
                #   is not received yet).
                #       So TCZee get a FIN-ACK that does not ACK the HTTP Response.
                #       At this point, the send_finAck is triggered and TCZee
                #   sends the FIN-ACK to close the connection
                #       but the TCZee SEQ number is wrong as it does not consider the
                #   ACKed response from client.
                #       I believe that also in case of a client that does not
                #   immediately send the FIN-ACK without ACKing
                #       the response, the correct value should be copied from pkt. Let's see.

                #self.l3[TCP].seq += len(self.last_packet[TCP].payload)
                #self.l3[TCP].payload = ""

            else:
                # If the data we need to send is bigger than 1024 B, we split it 
                # and make several calls to send()
                for chunk in chunkstring(self.toSend, 1024):
                    self.l3[TCP].seq = self.curSeq 
                    self.l3[TCP].ack = self.curAck
                    self.l3[TCP].payload = chunk
                    self.last_packet = self.l3
                    self.send(self.last_packet)
                    self.curSeq += chunk.__len__()
                    self.l3[TCP].payload = ""
                self.toSend = ""




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
            #print  "\n\t[isRetr] lastReceived ack: " + str(self.lastReceived[TCP].ack) +\
            #   ", seq: " + str(self.lastReceived[TCP].seq) +\
            #   ", payload: \"" + str( self.lastReceived[TCP].payload ) + "\""
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
            self.l3[TCP].dport = self.remotePort
            self.l3[TCP].sport = self.localPort

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

            if(pkt[TCP].ack > self.curSeq):
                self.curSeq = pkt[TCP].ack

            self.l3[TCP].seq = self.curSeq
            self.l3[TCP].ack = self.curAck

            self.lastReceived = pkt.copy()

#
    @ATMT.state(initial=1)
    def BEGIN(self):
#        pass
        self.l3 = IP()/TCP()
        self.preparePkt(self.initSYN)
        self.l3[TCP].flags = 'SA'
        self.send(self.l3)
        raise  self.SYNACK_SENT()

    @ATMT.state()
    def SYNACK_SENT(self):
        pass


    @ATMT.receive_condition(SYNACK_SENT)
    def receive_ackForSyn(self, pkt):
        if 'A' in flags(pkt[TCP].flags):
            self.preparePkt(pkt)
            raise self.ESTABLISHED()

    # Timeout: if I do not receive the ACK after 60 seconds sending the SYN ACK,
    # I go back to BEGIN (send again the SYN)
    # TODO this might be a good place to implement a retransmission logic,
    # for the moment it just keep tryin
    @ATMT.timeout(SYNACK_SENT, 4)
    def timeoutSynAckSent(self):

        self.curAck = 0
        self.curSeq = 0
        raise self.BEGIN()

    @ATMT.state()
    def ESTABLISHED(self):
        pass

    # Let's try to separate all these cases in separate conditions,
    # code should look better and TCZee.graph() would return a meaningful state chart diagram

    # in ESTABLISHED recv() FIN/ACK

    @ATMT.receive_condition(ESTABLISHED)
    def receive_finAck(self, pkt):
        # Check if the packet we got is a FIN/ACK
        # TODO  Make sure that in case of passive close we
        #   are expecting a FIN/ACK
        # TODO  It seems like if we make the & on 0x11, and ACK is enough to make it pass
        #   so we try to separate the checks on each flags. Check if this is true.
        #   One issue: it seems like the last ACK from the 3-way HS is somehow
        #   considered here also while running, even if I would expect this to
        #   already be consumed at this point in time
        if('F' in flags(pkt[TCP].flags)):
#        if TCP in pkt and (pkt[TCP].sport == self.dport) and (pkt[TCP].flags == 0x11):
            # TODO  here we will put the transition to the state CLOSING
            #   and the related action(CLOSING) will send the FIN/ACK and
            #   keep track of the sequence and ack numbers correctly. Check
            #   also TCP state diagram

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
        self.send(self.last_packet)

    # Receive RST while in ESTABLISHED
    @ATMT.receive_condition(ESTABLISHED)
    def receive_Rst(self, pkt):
        if('R' in flags(pkt[TCP].flags)):
            print "[DEBUG][ESTABLISHED] Received RST, ending TCZ"
            raise self.END()


    # Second condition based on split of ESTABLISHED receive data cases
    # in ESTABLISHED recv() PSH/ACK

    @ATMT.receive_condition(ESTABLISHED)
    def receive_pshAck(self, pkt):

        # check if the received packet is a PSH/ACK 0x18
        # TODO  EPIC this will need to consider also the case of HTTP requests splitted over
        #   multiple TCP segments, for the moment we assume request fits in one segment.
        #
        #   NOTES:  HTTP Request can be
        #
        #       - Without a body: The request is completed when
        #         you have 2 consecutives new lines
        #         0x0A 0x0D 0x0A 0x0D (but we should gracefully consider also LR only
        #
        #       - With a body: In this case, the request terminate
        #           - when the number of char indicated in Content-length is reached
        #           - according to the logic to handle the Chunked request
        #

        # TODO  Assuming that the HTTP data will be always contained in a TCP segment flagged as
        # httz  PSH/ACK, this is not necessarly true. In general all the data that arrives
        #   should be copied in the recv buffer

#        if TCP in pkt and (pkt[TCP].sport == self.dport) and (pkt[TCP].flags == 0x18):
        if ( ('P' in flags(pkt[TCP].flags)) and ('A' in flags(pkt[TCP].flags)) ): 

            # TODO  As of now, we are just assuming that the content of the TCP load
            #   is an HTTP request, this might be also something else in a more advanced version
            #   but if we need to start from somewhere, that's for sure HTTP(S)

            # TODO  Adding here a check to verify if we are already processing the request just
            #   received. Maybe we can go to another state (something like PROCESSING_REQUEST)
            #   to avoid that retransmission from the client mess-up the ACK counting. We clean
            #   this buffer when timeout, because I might want to make 2 consecutive requests for
            #   the same resource.

            if pkt[TCP].load and (not self.isRetransmit(pkt)) : #and (pkt[TCP].load != self.lastHttpRequest) :
                print "\t\t[DEBUG][ESTABLISHED] Received a request, and not a duplicate"
                self.preparePkt(pkt)
                # Adding the received load to the recv buffer
                self.recv.put( str( pkt[TCP].load ) )

                # We consume the content of the TCP load
                # by printing it, until we have an HTTZee to do something
                # more meaningful with it
                #print "\n[TCP Payload] " + self.receive()
                #print "\n"

                # self.preparePkt(pkt)

            # If received pkt has no load OR if the HTTP request is already received
            # in this case I do nothing
            # self.l3[TCP].seq = pkt[TCP].ack

            # Still in the assumption that whatever PSH/ACK TCP packet we receive from the client
            # will actually contains an HTTP request. Also, I am assuming that all the sizes goes
            # automatically with Scapy magic
            # TODO seems like sending the ACK for the request and the response in the same TCP segment
            # is not ok, trying to send them separatelly
            # self.l3[TCP] = httpResponse

            # ???   it is still not clear what is better in such a situation: put here the send() call
            #   or put it in the action related to this state? Question arises because based on
            #   content of the pkt I might need different actions triggered,
            #   without the change of state.
            #   Does this even make sense?
            #   I send here for the moment as I need to send the ACK but
            #   I do not need to change the state.
            #   This is different to the previous if case, for example,
            #   where also the state change.
            #
            # !!!   For the moment the best answer to this is that we should
            #   have a different ATMT.receive_condition
            #   for each case of the if, and send the response packet in
            #   the action of each condition.
            #   From code execution point of view maybe no difference in
            #   the 2 approaches, but thi separation
            #   allow to generate automatically a much more clear state diagram with TCZee.graph()

                    # self.l3 = self.l3/httpResponse
            # self.responseReady = 1
            # Just want to move the send() call into the related ATMT.action, just to keep
            # the code clean and according to state machine formalism

                raise self.ESTABLISHED()


    @ATMT.action(receive_pshAck)
    def sendAck(self):
        self.l3[TCP].flags = 'A'
        self.last_packet = self.l3
        self.send(self.last_packet)

    # in ESTABLISHED recv() a SYN (basically client want to start a new tcp stream)


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
            # NOTE: Go again back to LISTEN, in order to be able to handle several request with the same
            #   instance of TCZ/HTTZ. If a client sends a request and close the connection when te response
            #   is received (for example, because of 'Connection: close' header), this will terminate the
            #   main script, so a second request will not find anything listening for it.
        #else:
        #   # something else received
        #   # DEBUG
        #   print "\t\t[DEBUG][CLOSING] We receive something that is not an ACK: " + pkt.summary()
        #   pass
    # After timeout in CLOSING, terminate (basically only one FIN from
    # the client is enough to close connection
    # TODO  THIS IS WRONG!

    @ATMT.timeout(CLOSING, 5)
    def timeoutClosing(self):
        self.l3[TCP].ack = 0
        self.l3[TCP].seq = 0
        self.l3[TCP].payload = ""
        self.last_packet = self.l3
        raise self.END()

    # This is simply a final state to have an exit condition
    # once the TCP terminate connection is completed

    @ATMT.state(final=1)
    def END(self):
        pass


class HTTZee(object):

    def __init__(self, tcz):
        # Threading stuff

        # Adding a reference to the TCZ used as TCP stack
        self.tcz = tcz

        self.resources = {}

        self.createHTTZ(tcz)

    def createHTTZ(self, tczParam):
        body = "Example of Content category TestCase content."
        bodySize = body.__len__()

        if(tczParam.jsonConfig != {} and tczParam.jsonConfig['resources'] != "" ):

            for res in self.tcz.jsonConfig['resources']:

                bodySize = res['body'].__len__()

                # NOTE: We need to dinamically calculate the size of body and add the Content-length header.
                # TODO: For the moment we assume that this header is not in the JSON file, we might
                #   add a mechanism to check if the header is presentinthe JSON and replace it with the
                #   dinamically calculated value.
                #   Check re module for regular expression (str.replace() does not understand regex)
                headers = res['headers']
                headers = headers.rstrip()
                headers += "\r\nContent-length: " + str(bodySize) + "\r\n\r\n"

                self.resources[res['resource']] = str(headers + res['body'])

        else:
            print "[ERROR] HTTZee initialized without correct JSON config file. No resources available."
            exit()

    def connection(self):
        print "\t[HTTZ][connection()] Starting TCZee thread  -- current Thread --%s"%(threading.current_thread().name)
        self.tcz.run()

    def run(self):
        s = ""
        print "\t[HTTZ][run()] called TCZee.run(), entering infinite loop now.-- current Thread --%s"%(threading.current_thread().name)
        while ( s != "exit" ):
            # We will need a call to recv() instead of directly
            # accessing the TCZ Queue, but for the moment this is
            # fine. This is a blocking call.
            s = str( self.tcz.recv.get() )
            print "\t[HTTZ][run()] Received data: " + s + "-- current Thread --" + (threading.current_thread().name) +"\n"
            self.processRequest(s)

    def processRequest(self, req):
        # TODO  Here we will need the logic to parse the whole HTTP request
        #   and return the requested resource. This include the logic to
        #   parse HTTP Header, URL parameters and body.
        #   No need to re-invent the wheel here, we can use existing libraries.
        #
        #   For the sake of the demo, we assume now req contains the whole
        #   HTTP request

        for p in req.split():
                        # print "\t[HTTZ] spliting request:" + p
            if (p in self.resources.keys() ):
                print "\t[HTTZ][processRequest] Matching resource, sending response: " + self.resources[p]+ " -- current Thread --" + (threading.current_thread().name) +"\n"
                self.tcz.write(self.resources[p])
                                # Added by bdesikan on 18-Sep-16 during debug session
                                # Temporary Patch to fix the mismatch in th Ack number
                                # due to synchronization issue between the TCZ and HTTZ components.
                                #TODO: Fix using robust approah
                                # time.sleep(1)
                self.tcz.send_response()

        #return self.resources[req]


#TCZee.graph()
#t = TCZee(80, debug=3)
#t.run()

class Connector(Automaton):
    def parse_args(self, jsonConfig={}, **kargs):
        Automaton.parse_args(self, **kargs)
        self.config = jsonConfig

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

    # BEGIN state
    @ATMT.state(initial=1)
    def CON_BEGIN(self):
        raise self.CON_LISTEN()

    @ATMT.state()
    def CON_LISTEN(self):
        pass

    @ATMT.receive_condition(CON_LISTEN)
    def con_receive_syn(self, pkt):
        if('S' in flags(pkt[TCP].flags)):
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
                tcz = TCZee(self.config, pkt, debug=3)
                tczThread = Thread(target=tcz.run, name='tcz_Thread_Packet')
                tczThread.deamon = True
                tczThread.start()
                

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
