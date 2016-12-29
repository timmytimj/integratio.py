# content of test_dns.py

# Reference for building the test case
# you must install the dnspython module to make 
# dns querying from within the python code

# Ref-Site fro dnspython lib: http://www.dnspython.org/

import dns.resolver
from dns.resolver import NXDOMAIN
from dns.exception import DNSException


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
import IN

confi = {
    "test-id"  : "dns001",\
    "interface": "lo",\
    "lis-port" : 53,\
    "category" : "dns",\
    "parameter": [\
        {\
            "q-addr" : "www.google.com",\
            "response": "192.168.178.60"\
        },\
        {\
            "q-addr" : "www.test.com",\
            "response": "192.168.178.68"\
        }\
    ]\
}

my_IPaddress = get_my_IPaddress( confi['interface'] )

@pytest.fixture
def domain_found_1():
    con = Connector(confi, debug=3)
    con.runbg()
    myResolver = dns.resolver.Resolver()
    myResolver.nameservers = [my_IPaddress]
    myAnswers = myResolver.query("www.test.com", "A")
    for rdata in myAnswers:
        yield rdata.address
    con.stop()

@pytest.fixture
def domain_found_2():
    con = Connector(confi, debug=3)
    con.runbg()
    myResolver = dns.resolver.Resolver()
    myResolver.nameservers = [my_IPaddress]
    myAnswers = myResolver.query("www.google.com", "A")
    for rdata in myAnswers:
        yield rdata.address
    con.stop()

@pytest.fixture
def domain_not_found():
    con = Connector(confi, debug=3)
    con.runbg()
    yield con
    con.stop()

# DNZ

# This test case verifies the basic dns query for "dns" category
def test_domain_found_1(domain_found_1):
    assert  domain_found_1=="192.168.178.68"

def test_domain_found_2(domain_found_2):
    assert  domain_found_2=="192.168.178.60"

def test_domain_not_found(domain_not_found):
    myResolver = dns.resolver.Resolver()
    myResolver.nameservers = [my_IPaddress]
    try:
        myResolver.query("www.google1.com", "A")
    except NXDOMAIN:
        assert  True
    except DNSException:
        assert False
    else:
        assert False

