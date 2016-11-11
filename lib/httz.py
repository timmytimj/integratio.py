from scapy.all import *
#from tcz import TCPConnection
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
