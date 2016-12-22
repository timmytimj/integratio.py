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

config = {
    "testID" : "Content test case 1",\
    "category" : "content",\
    "state" :"LISTEN",\
    "parameter" : 6,\
    "listeningPort" : 80,\
    "listeningAddress" : "testing.com",\
    "listeningInterface" : "eth0",\
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
                                        "headers"       : "HTTP/1.1 404 Resource not found\r\nConnection: close\r\nDate: Sat, 27 Aug 2016 18:51:19 GMT\r\nServer: Apache/2.4.10 (Unix)\r\n"\
                                },\
                {\
                                        "resource"      : "/favicon.ico",\
                                        "body"      : "FavICO",\
                    "headers"       : "HTTP/1.1 200 OK\r\nConnection: close\r\nDate: Sat, 27 Aug 2016 18:51:19 GMT\r\nServer: Apache/2.4.10 (Unix)\r\n"\
                                }\
            ]\
}



@pytest.fixture
def makeRequest500():
    # Starting the Connector thread
#    fileConfig = io.open('../configs/content.json')
#    config = json.load(fileConfig)
    con = Connector(config, debug=3)
    con.runbg()

    my_IPaddress = "http://%s" % (get_my_IPaddress('eth0'))

    r = requests.get(my_IPaddress + '/500', timeout=5)
    yield r
    r.close()
    con.stop()

@pytest.fixture
def makeRequest404():
    # Starting the Connector thread
#    fileConfig = io.open('../configs/content.json')
#    config = json.load(fileConfig)
    con = Connector(config, debug=3)
    con.runbg()

    my_IPaddress = "http://%s" % (get_my_IPaddress('eth0'))

    r = requests.get(my_IPaddress + '/404', timeout=5)
    yield r
    r.close()
    con.stop()

#    def setup_method(self, test_content_500):
#        fileConfig = io.open('../configs/content.json')
#        config = json.load(fileConfig)
#        con = tcz.Connector(config, debug=3)
#        con.run()

def test_content_500(makeRequest500):
    assert makeRequest500.status_code == 500

def test_content_404(makeRequest404):
    assert makeRequest404.status_code == 404        
