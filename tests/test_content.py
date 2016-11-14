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
def makeRequest500():
    # Starting the Connector thread
    fileConfig = io.open('../configs/content.json')
    config = json.load(fileConfig)
    con = tcz.Connector(config, debug=3)
    con.runbg()


    r = requests.get('http://192.168.13.1/500', timeout=2)
    yield r
    r.close()
    con.stop()

@pytest.fixture
def makeRequest404():
    # Starting the Connector thread
    fileConfig = io.open('../configs/content.json')
    config = json.load(fileConfig)
    con = tcz.Connector(config, debug=3)
    con.runbg()


    r = requests.get('http://192.168.13.1/404', timeout=2)
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
