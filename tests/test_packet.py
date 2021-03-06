# content of test_packet.py

# Just a reference while building the test case
#    ICMP type=3, code=1 -> EHOSTUNREACH
#    ICMP type=3, code=2 -> ENOPROTOOPT
#    ICMP type=3, code=3 -> ECONNREFUSED
#    ICMP type=3, code=4 -> No error
#    ICMP type=3, code=5 -> ENOTSUP
#    ICMP type=3, code=6 -> ENETUNREACH
#    ICMP type=3, code=7 -> EHOSTDOWN
#    ICMP type=3, code=8 -> ENONET

import sys
sys.path.append('../libs')
from connector import Connector
from get_my_IPaddress import get_my_IPaddress
import requests
import pytest
import io
import json
import time
import socket
import errno
import IN

confi = {
    "test-id"   : "General test 1",
    "interface" : "eth0",
    "tcp-port"  : 80,
    "configs"     : [
        {
            "category"  : "packet",
            "parameters": [
                {
                    "sub-category" : "tcz",
                    "state"     : "ESTABLISHED",
                    "action"    : "sendAck",
                    "flags"     : "RPA"
                }
            ]
        }
    ]
}
 
my_IPaddress = get_my_IPaddress( confi['interface'] )

def send( server_address = (my_IPaddress, 80) ):
    time.sleep(0.5)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt( socket.IPPROTO_IP, IN.IP_RECVERR, 1 )
    sock.settimeout(7)
    sock.connect(server_address)
    sock.send("Ciao caro")
    time.sleep(1)
    return sock.send("Ciao di nuovo")

@pytest.fixture
def runConnector():
    con = Connector(confi, debug=3)
    con.runbg()
    return con
#    yield  con
#    con.stop()
#    time.sleep(0.4)

@pytest.fixture
def runConnectorRefused():
    confi['configs'][0]['parameters'][0]['state'] = 'BEGIN'
    confi['configs'][0]['parameters'][0]['action'] = 'BEGIN'
    confi['configs'][0]['parameters'][0]['flags'] = 'RPA'
    con = Connector(confi, debug=3)
    con.runbg()
    return con
#    yield  con
#    con.stop()
#    time.sleep(0.4)

@pytest.fixture
def runConnectorEHOSTUNREACH():
    confi['configs'][0]['parameters'][0]['sub-category'] = 'icmz'
    confi['configs'][0]['parameters'][0]['state'] = 'ESTABLISHED'
    confi['configs'][0]['parameters'][0]['action'] = 'sendAck'
    confi['configs'][0]['parameters'][0]['type'] = 3
    confi['configs'][0]['parameters'][0]['code'] = 1
    con = Connector(confi, debug=3)
    con.runbg()
    return con
#    yield  con
#    con.stop()
#    time.sleep(0.4)

@pytest.fixture
def runConnectorENOPROTOOPT():
    confi['configs'][0]['parameters'][0]['sub-category'] = 'icmz'
    confi['configs'][0]['parameters'][0]['state'] = 'ESTABLISHED'
    confi['configs'][0]['parameters'][0]['action'] = 'sendAck'
    confi['configs'][0]['parameters'][0]['type'] = 3
    confi['configs'][0]['parameters'][0]['code'] = 2
    con = Connector(confi, debug=3)
    con.runbg()
    return con
#    yield  con
#    con.stop()
#    time.sleep(0.4)

@pytest.fixture
def runConnectorECONNREFUSED():
    confi['configs'][0]['parameters'][0]['sub-category'] = 'icmz'
    confi['configs'][0]['parameters'][0]['state'] = 'ESTABLISHED'
    confi['configs'][0]['parameters'][0]['action'] = 'sendAck'
    confi['configs'][0]['parameters'][0]['type'] = 3
    confi['configs'][0]['parameters'][0]['code'] = 3    
    con = Connector(confi, debug=3)
    con.runbg()
    return con
#    yield  con
#    con.stop()
#    time.sleep(0.4)

@pytest.fixture
def runConnectorENOTSUP():
    confi['configs'][0]['parameters'][0]['sub-category'] = 'icmz'
    confi['configs'][0]['parameters'][0]['state'] = 'ESTABLISHED'
    confi['configs'][0]['parameters'][0]['action'] = 'sendAck'
    confi['configs'][0]['parameters'][0]['type'] = 3
    confi['configs'][0]['parameters'][0]['code'] = 5
    con = Connector(confi, debug=3)
    con.runbg()
    return con
#    yield  con
#    con.stop()
#    time.sleep(0.4)

@pytest.fixture
def runConnectorENETUNREACH():
    confi['configs'][0]['parameters'][0]['sub-category'] = 'icmz'
    confi['configs'][0]['parameters'][0]['state'] = 'ESTABLISHED'
    confi['configs'][0]['parameters'][0]['action'] = 'sendAck'
    confi['configs'][0]['parameters'][0]['type'] = 3
    confi['configs'][0]['parameters'][0]['code'] = 6
    con = Connector(confi, debug=3)
    con.runbg()
    return con
#    yield  con
#    con.stop()
#    time.sleep(0.4)

@pytest.fixture
def runConnectorEHOSTDOWN():
    confi['configs'][0]['parameters'][0]['sub-category'] = 'icmz'
    confi['configs'][0]['parameters'][0]['state'] = 'ESTABLISHED'
    confi['configs'][0]['parameters'][0]['action'] = 'sendAck'
    confi['configs'][0]['parameters'][0]['type'] = 3
    confi['configs'][0]['parameters'][0]['code'] = 7
    con = Connector(confi, debug=3)
    con.runbg()
    return con
#    yield  con
#    con.stop()
#    time.sleep(0.4)

@pytest.fixture
def runConnectorENONET():
    confi['configs'][0]['parameters'][0]['sub-category'] = 'icmz'
    confi['configs'][0]['parameters'][0]['state'] = 'ESTABLISHED'
    confi['configs'][0]['parameters'][0]['action'] = 'sendAck'
    confi['configs'][0]['parameters'][0]['type'] = 3
    confi['configs'][0]['parameters'][0]['code'] = 8
    con = Connector(confi, debug=3)
    con.runbg()
    return con
#    yield  con
#    con.stop()
#    time.sleep(0.4)

# TCZ

# This test case verifies that the connection
# is reset by the server side (RST sent between 2 send() )
def test_packet_tcz_1(runConnector):
    try:
        send()
    except socket.error, v:
        errorcode = v[0]
        assert errorcode == errno.ECONNRESET

# This test case verifies that the connection establishment
# is reset by the server side (RST sent before SYN ACK )
# NOTE  I need to send a RST PSH ACK (PSH is just to pass through the
#       iptables rule) because without the ACK the connect() will just
#       timeout, but not ECONNREFUSED
def test_packet_tcz_2(runConnectorRefused):
    try:
        send()
    except socket.error, v:
        errorcode = v[0]
        assert errorcode == errno.ECONNREFUSED

# ICMP

# This test case verifies that the socket client fails with EHOSTUNREACH
# when try to send() after receiving an ICMP error type 3 code 1.
# This happens only if the socket has the IP_RECVERR option enabled, 
# and this is not the default
def test_packet_icmp_1(runConnectorEHOSTUNREACH):
    try:
        send()
    except socket.error, v:
        errorcode = v[0]
        assert errorcode == errno.EHOSTUNREACH

# ICMP type 3 code 2 ENOPROTOOPT
def test_packet_icmp_2(runConnectorENOPROTOOPT):
    try:
        send()
    except socket.error, v:
        errorcode = v[0]
        assert errorcode == errno.ENOPROTOOPT

# ICMP type 3 code 3 ECONNREFUSED
def test_packet_icmp_3(runConnectorECONNREFUSED):
    try:
        send()
    except socket.error, v:
        errorcode = v[0]
        assert errorcode == errno.ECONNREFUSED

# ICMP type 3 code 5 ENOTSUP
def test_packet_icmp_5(runConnectorENOTSUP):
    try:
        send()
    except socket.error, v:
        errorcode = v[0]
        assert errorcode == errno.ENOTSUP

# ICMP type 3 code 6 ENETUNREACH
def test_packet_icmp_6(runConnectorENETUNREACH):
    try:
        send()
    except socket.error, v:
        errorcode = v[0]
        assert errorcode == errno.ENETUNREACH

# ICMP type 3 code 7 EHOSTDOWN
def test_packet_icmp_7(runConnectorEHOSTDOWN):
    try:
        send()
    except socket.error, v:
        errorcode = v[0]
        assert errorcode == errno.EHOSTDOWN

# ICMP type 3 code 8 ENONET
def test_packet_icmp_8(runConnectorENONET):
    try:
        send()
    except socket.error, v:
        errorcode = v[0]
        assert errorcode == errno.ENONET

