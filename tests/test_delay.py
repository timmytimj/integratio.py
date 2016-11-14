# content of test_delay.py

import sys
sys.path.append('../lib')
import tcz 
import requests
import pytest
import io
import json
import time
import socket
from connector import Connector

config = { \
    "testID" : "Delay02", \
    "category" : "time", \
    "state" :"BEGIN", \
    "action":"BEGIN",\
    "parameter" : 3, \
    "listeningPort" : 80, \
    "listeningAddress" : "testing.com", \
    "listeningInterface" : "wlan0" \
}


def connect( time = 3, server_address = ('192.168.13.1', 80) ):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(time)
    sock.connect(server_address)

# Same as connect(), just return an error code instead of 
# raising an exception if the connection fails
def connect_ex( time = 3, server_address = ('192.168.13.1', 80) ):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(time)
    return sock.connect_ex(server_address)



@pytest.fixture
def runConnector():
    # Starting the Connector thread
#    fileConfig = io.open('../configs/delay.json')
#    config = json.load(fileConfig)
    con = Connector(config, debug=3)
    con.runbg()
    yield  con
    con.stop()

# TCZ will wait 3 seconds before reply to SYN.
# connect has a timeout of 1 in this test case.
# TEST PASS if the connect(1) raise the Timeout
# exception 

def test_delay1(runConnector):
    with pytest.raises(socket.timeout):
        connect(2)

# In this case, the connection should happen 
# correctly
def test_delay2(runConnector):
    assert connect_ex(5) == 0
    


