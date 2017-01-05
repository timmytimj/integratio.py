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

config = {\
    "test-id"   : "General test 1",\
    "interface" : "eth0",\
    "tcp-port"  : 80,\
    "configs"     : [\
        {\
            "category"  : "content",\
            "parameters": [\
                {\
                        "resource"  : "/",\
                        "http-status" : "HTTP/1.1 200 OK\r\n",\
                        "body"      : "Response for the main resource /",\
                        "headers"   : "Connection: close\r\nDate: Sat, 27 Aug 2016 18:51:19 GMT\r\nServer: Apache/2.4.10 (Unix)\r\n"\
                },\
                {\
                        "resource"      : "/500",\
                        "http-status"   : "HTTP/1.1 500 Internal Server error\r\n",\
                        "body"          : "Response for the 500 error",\
                        "headers"       : "Connection: close\r\nDate: Sat, 27 Aug 2016 18:51:19 GMT\r\nServer: Apache/2.4.10 (Unix)\r\n"\
                },\
                {\
                        "resource"      : "/404",\
                        "body"          : "Response for the 404 error",\
                        "http-status" : "HTTP/1.1 404 Resource Not Found\r\n",\
                        "headers"       : "Connection: close\r\nDate: Sat, 27 Aug 2016 18:51:19 GMT\r\nServer: Apache/2.4.10 (Unix)\r\n"\
                },\
                {\
                        "resource"      : "/favicon.ico",\
                        "http-status"   : "HTTP/1.1 200 OK\r\n",\
                        "body"          : "FavICO",\
                        "headers"       : "Connection: close\r\nDate: Sat, 27 Aug 2016 18:51:19 GMT\r\nServer: Apache/2.4.10 (Unix)\r\n"\
                }\
            ]\
        }\
    ]\
} 



@pytest.fixture
def makeRequestMultiConnections():
    # Starting the Connector thread
    # fileConfig = io.open('../configs/content.json')
    # config = json.load(fileConfig)
    con = Connector(config, debug=3)
    con.runbg()

    my_IPaddress = "http://%s" % (get_my_IPaddress('eth0'))

    # creating MULTIPLE requests
    r1 = requests.get(my_IPaddress + '/500', timeout=2)
    r2 = requests.get(my_IPaddress + '/404', timeout=2)
    r3 = requests.get(my_IPaddress + '/favicon.ico', timeout=2)
    yield r1, r2, r3
    r1.close()
    r2.close()
    r3.close()
    con.stop()


def test_multiConnections(makeRequestMultiConnections):
    # Asserting the response for resource "/500"
    assert makeRequestMultiConnections[0].status_code == 500
    assert makeRequestMultiConnections[0].content == "Response for the 500 error"
    assert makeRequestMultiConnections[0].headers == {'Date': 'Sat, 27 Aug 2016 18:51:19 GMT', 'Connection': 'close', 'Content-length': '26', 'Server': 'Apache/2.4.10 (Unix)'}

    # Asserting the response for resource "/404"
    assert makeRequestMultiConnections[1].status_code == 404
    assert makeRequestMultiConnections[1].content == "Response for the 404 error"
    assert makeRequestMultiConnections[1].headers == {'Date': 'Sat, 27 Aug 2016 18:51:19 GMT', 'Connection': 'close', 'Content-length': '26', 'Server': 'Apache/2.4.10 (Unix)'}

    # Asserting the response for resource "/favicon.ico"
    assert makeRequestMultiConnections[2].status_code == 200
    assert makeRequestMultiConnections[2].content == "FavICO"
    # actual header in json = {'Date: Sat, 27 Aug 2016 18:51:19 GMT\r\nServer: Apache/2.4.10 (Unix)'} ????
    assert makeRequestMultiConnections[2].headers == {'Date': 'Sat, 27 Aug 2016 18:51:19 GMT', 'Connection': 'close', 'Content-length': '6', 'Server': 'Apache/2.4.10 (Unix)'}
