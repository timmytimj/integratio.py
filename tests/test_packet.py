# content of test_packet.py

import sys
sys.path.append('../lib')
import tcz 
import requests
import pytest
import io
import json
import time
import socket



def connectAndSend( data = "ciao", time = 3, server_address = ('192.168.13.1', 80) ):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(time)
    sock.connect(server_address)
    sock.send(data)

# Same as connect(), just return an error code instead of 
# raising an exception if the connection fails
def connect_ex( time = 3, server_address = ('192.168.13.1', 80) ):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(time)
    return sock.connect_ex(server_address)



@pytest.fixture
def runConnector():
    # Starting the Connector thread
    fileConfig = io.open('../configs/packet.json')
    config = json.load(fileConfig)
    con = tcz.Connector(config, debug=3)
    con.runbg()
    return con

def test_delay1(runConnector):
#    with pytest.raises(socket.timeout):
        connectAndSend("Ciao Cazzello!")
