# content of test_packet.py

import sys
sys.path.append('../lib')
import requests
import pytest
import io
import json
import time
import socket
from connector import Connector
import errno

confi = {
    "testID" : "Packet001",
    "category" : "packet",
    "state" : "ESTABLISHED",
    "action" :"sendAck",
    "parameter" : "RP",
    "listeningPort" : 80,
    "listeningAddress" : "testing.com",
    "listeningInterface" : "eth0"
}

def send( server_address = ('192.168.178.60', 80) ):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect(server_address)
    sock.send("Ciao caro")
    time.sleep(1)
    return sock.send("Ciao di nuovo")

@pytest.fixture
def runConnector():
    con = Connector(confi, debug=3)
    con.runbg()
    yield  con
    con.stop()

@pytest.fixture
def runConnectorRefused():
    confi['state'] = 'BEGIN'
    confi['action'] = 'BEGIN'
    confi['parameter'] = 'RPA'
    con = Connector(confi, debug=3)
    con.runbg()
    yield  con
    con.stop()



# This test case verifies that the connection
# is reset by the server side (RST sent between 2 send() ) 
 
def test_packet_1(runConnector):
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
def test_packet_2(runConnectorRefused):
    try:
        send()
    except socket.error, v:
        errorcode = v[0]
        assert errorcode == errno.ECONNREFUSED






