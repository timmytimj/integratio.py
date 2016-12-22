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

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

# Use RawSocket to make it work on local interface to.
#
# NOTE  Raw Socket usage was giving a problem with Operation not permitted
#       but that was actually due to the iptables rules to block RST.
#       This has been fixed by changing the iptable rule.
#       Still would be interesting to understand how using PacketSocket
#       the iptable rules did not apply.
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

# Tool method to check if the current test is relevant
# for the current STATE and Action
def isTestRelevant(config, category, state, action):
    ret = False
    if 'category' in config and config['category'] == category:
        if 'state' in config and config['state'] == state:
            if 'action' in config and config['action'] == action:
                ret = True

    return ret

class tConf(object):
    def __init__(self, state = "ESTABLISHED", action = "sendAck"):
        self.state = state
        self.action = action
        
class confDelay(tConf):
    def __init__(self, state = "ESTABLISHED", action = "sendAck", time = 3):
        self.time = time
        super(confDelay, self).__init__(state, action)

class confTCZ(tConf):
    def __init__(self, state = "ESTABLISHED", action = "sendAck", flags = 'R'):
        self.flags = flags
        super(confTCZ, self).__init__(state, action)

class confICMZ(tConf):
    def __init__(self, state = "ESTABLISHED", action = "sendAck", typ = 3, code = 3):
        self.typ = typ
        self.code = code
        super(confICMZ, self).__init__(state, action)


















