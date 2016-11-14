# content of test_ports.py

import sys
sys.path.append('../lib')
import tcz 
import requests
import pytest
import io
import json
import time
import socket



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
    fileConfig = io.open('../configs/delay_52413.json')
    config = json.load(fileConfig)
    con = tcz.Connector(config, debug=3)
    con.runbg()
    return con

# This test pass if connection is succesfull 
# on the specific port
def test_port_ok(runConnector):
    assert connect_ex(2, ('192.168.13.1', 52413)) == 0
    

# This test pass is the connection on
# port 80 fails (because the json config
# is set to listen on 52413
def test_port_connFails(runConnector):
    assert connect_ex(2) != 0




