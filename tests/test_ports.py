# content of test_ports.py

import sys
sys.path.append('../libs')
from connector import Connector
from get_my_IPaddress import get_my_IPaddress
import tcz 
import requests
import pytest
import io
import json
import time
import socket


config = {\
    "testID" : "Delay01",\
    "category" : "time",\
    "state" :"LISTEN",\
    "parameter" : 6,\
    "listeningPort" : 52413,\
    "listeningAddress" : "testing.com",\
    "listeningInterface" : "eth0"\
}

my_IPaddress = get_my_IPaddress('eth0')

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
#    fileConfig = io.open('../configs/delay_52413.json')
#    config = json.load(fileConfig)
    con = Connector(config, debug=3)
    con.runbg()
    yield con
    con.stop()

# This test pass if connection is succesfull 
# on the specific port
def test_port_ok(runConnector):
    assert connect_ex(2, (my_IPaddress, 52413)) == 0
    

# This test pass is the connection on
# port 80 fails (because the json config
# is set to listen on 52413
def test_port_connFails(runConnector):
    assert connect_ex(2) != 0




