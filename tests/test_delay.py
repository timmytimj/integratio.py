# content of test_delay.py

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


config = { \
    "testID" : "Delay02", \
    "category" : "time", \
    "state" :"BEGIN", \
    "action":"BEGIN",\
    "parameter" : 3, \
    "listeningPort" : 80, \
    "listeningAddress" : "testing.com", \
    "listeningInterface" : "lo" \
}

my_IPaddress = get_my_IPaddress('lo')

def connect( time = 3, server_address = (my_IPaddress, 80) ):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(time)
    sock.connect(server_address)

# Same as connect(), just return an error code instead of 
# raising an exception if the connection fails
def connect_ex( time = 3, server_address = (my_IPaddress, 80) ):
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
# exception.
#
# NOTE: Not clear why but here the connect_ex return 
#       errno 11 (EAGAIN), but the exception name raised
#       by connect() is timeout. This is not clear but
#       I'll mark the test case to cover the timeout.

def test_delay_1(runConnector):
    with pytest.raises(socket.timeout):
#    try:
        connect(2)
#    except socket.error, v:
#        errorcode = v[0]
#        assert errorcode == 110




# In this case, the connection should happen 
# correctly
def test_delay_2(runConnector):
    assert connect_ex(5) == 0
