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
