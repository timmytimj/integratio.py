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


config = {
    "test-id"   : "General test 1",
    "interface" : "eth0",
    "tcp-port"  : 80,
    "configs"     : [
        {
            "category"  : "time",
            "parameters": [
                {
                    "state"     : "BEGIN",
                    "action"    : "BEGIN",
                    "delay"     : 3
                },
                {
                    "state"     : "ESTABLISHED",
                    "action"    : "sendAck",
                    "delay"     : 3
                },
                {
                    "state"     : "ESTABLISHED",
                    "action"    : "send_response",
                    "delay"     : 3
                }
            ]
        },
        {
            "category" : "content",
            "parameters": [
                {
                    "resource"  : "/delay.html",
                    "http-status" : "HTTP/1.1 200 OK\r\n",
                    "body"      : "This is a delayed, valid HTTP response.",
                    "headers"   : "Connection: close\r\nDate: Sat, 27 Aug 2016 18:51:19 GMT\r\nServer: Apache/2.4.10 (Unix)\r\n"
                }
            ]
        }
    ]
}

my_IPaddress = get_my_IPaddress(config['interface'])

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
    con = Connector(config, debug=3)
    con.runbg()
    time.sleep(1)
    return  con

# TCZ will wait 3 seconds before reply to SYN.
# connect has a timeout of 1 in this test case.
# TEST PASS if the connect(1) raise the Timeout
# exception.

# NOTE: Not clear why but here the connect_ex return 
#       errno 11 (EAGAIN), but the exception name raised
#       by connect() is timeout. This is not clear but
#       I'll mark the test case to cover the timeout.

def test_delay_1(runConnector):
    with pytest.raises(socket.timeout):
        connect(1)

# In this case, the connection should happen 
# correctly
def test_delay_2(runConnector):
    assert connect_ex(5) == 0

# This test verify the delay in sending an HTTP response
def test_delay_3(runConnector):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect((my_IPaddress, 80))
    sock.send("get /delay.html")
    start = time.time()
    print sock.recv(1024)
    end = time.time()

    assert (end - start) > 2
    
