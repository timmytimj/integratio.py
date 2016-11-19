# content of test_delay.py

import sys
sys.path.append('../lib')
from connector import Connector
import requests
import pytest
import io
import json
import time

config = {
    "testID" : "Content test case 1",\
    "category" : "content",\
    "state" :"LISTEN",\
    "parameter" : 6,\
    "listeningPort" : 80,\
    "listeningAddress" : "testing.com",\
    "listeningInterface" : "wlan0",\
    "resources" :   [\
                {\
                    "resource"  : "/",\
                    "body"      : "Response for the main resource /",\
                    "headers"   : "HTTP/1.1 200 OK\r\nConnection: close\r\nDate: Sat, 27 Aug 2016 18:51:19 GMT\r\nServer: Apache/2.4.10 (Unix)\r\n"\
                },\
                {\
                                        "resource"      : "/500",\
                                        "body"          : "Response for the 500 error",\
                                        "headers"       : "HTTP/1.1 500 Internal server error\r\nConnection: close\r\nDate: Sat, 27 Aug 2016 18:51:19 GMT\r\nServer: Apache/2.4.10 (Unix)\r\n"\
                                },\
                {\
                                        "resource"      : "/404",\
                                        "body"          : "Response for the 404 error",\
                                        "headers"       : "HTTP/1.1 404 Resource not found\r\nConnection: close\r\nDate: Mon, 28 Nov 2016 18:51:19 GMT\r\nServer: Apache/2.4.10 (Unix)\r\n"\
                                },\
                {\
                                        "resource"      : "/favicon.ico",\
                                        "body"      : "FavICO",\
                                        "headers"       : "HTTP/1.1 200 OK\r\nConnection: close\r\nDate: Sat, 27 Aug 2016 18:51:19 GMT\r\nServer: Apache/2.4.10 (Unix)\r\n"\
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

    # creating MULTIPLE requests
    r1 = requests.get('http://192.168.0.241/500', timeout=2)
    r2 = requests.get('http://192.168.0.241/404', timeout=2)
    r3 = requests.get('http://192.168.0.241/favicon.ico', timeout=2)
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
    assert makeRequestMultiConnections[1].headers == {'Date': 'Mon, 28 Nov 2016 18:51:19 GMT', 'Connection': 'close', 'Content-length': '26', 'Server': 'Apache/2.4.10 (Unix)'}

    #import pdb; pdb.set_trace()
    # Asserting the response for resource "/favicon.ico"
    assert makeRequestMultiConnections[2].status_code == 200
    assert makeRequestMultiConnections[2].content == "FavICO"
    # actual header in json = {'Date: Sat, 27 Aug 2016 18:51:19 GMT\r\nServer: Apache/2.4.10 (Unix)'} ????
    assert makeRequestMultiConnections[2].headers == {'Date': 'Sat, 27 Aug 2016 18:51:19 GMT', 'Connection': 'close', 'Content-length': '6', 'Server': 'Apache/2.4.10 (Unix)'}
