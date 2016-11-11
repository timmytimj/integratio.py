# content of test_delay.py

import sys
sys.path.append('../lib')
import tcz 
import requests
import pytest
import io
import json
import time

@pytest.fixture
def makeRequest():
    # Starting the Connector thread
    fileConfig = io.open('../configs/content.json')
    config = json.load(fileConfig)
    con = tcz.Connector(config, debug=3)
    con.runbg()


    r = requests.get('http://192.168.13.1/500', timeout=2)
    yield r
    r.close()
    con.stop()


#    def setup_method(self, test_content_500):
#        fileConfig = io.open('../configs/content.json')
#        config = json.load(fileConfig)
#        con = tcz.Connector(config, debug=3)
#        con.run()

def test_content_500(makeRequest):
    assert makeRequest.status_code == 500
        
