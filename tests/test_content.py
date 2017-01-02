# content of test_content.py

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
    "lis-port" : 80,\
    "interface" : "eth0",\
    "parameter" :   [\
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
