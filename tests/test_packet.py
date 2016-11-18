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

# Same as connect(), just return an error code instead of 
# raising an exception if the connection fails
#def connect_ex( time = 3, server_address = ('192.168.13.1', 80) ):
#    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#    sock.settimeout(time)
#    return sock.connect_ex(server_address)



@pytest.fixture
def runConnector():
    # Starting the Connector thread
#    fileConfig = io.open('../configs/delay.json')
#    config = json.load(fileConfig)
    con = Connector(confi, debug=3)
    con.runbg()
    yield  con
    con.stop()



# This test case verifies that 
# 
def test_packet_1(runConnector):
    try:
        send()
    except socket.error, v:
        errorcode = v[0]
        assert errorcode == errno.ECONNRESET
        





