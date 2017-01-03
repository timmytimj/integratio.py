#!/usr/bin/python

import json
from scapy.all import *
import sys
sys.path.append('.')
from libs.connector import Connector

log_interactive.setLevel(1)

jconfig = config = {\
    "test-id"   : "General test 1",\
    "interface" : "eth0",\
    "tcp-port"  : 80,\
    "dns-port"  : 53,\
    "configs"     : [\
        {\
            "category"  : "time",\
            "parameters": [\
                {\
                    "state"     : "BEGIN",\
                    "action"    : "BEGIN",\
                    "delay"     : 6\
                }\
            ]\
        },\
        {\
            "category"  : "packet",\
            "parameters": [\
                {\
                    "sub-category" : "tcz",\
                    "state"     : "ESTABLISHED",\
                    "action"    : "send_finAck",\
                    "flags"     : "RP"\
                }\
#                {\
#                    "sub-category" : "icmz",\
#                    "state"     : "ESTABLISHED",\
#                    "action"    : "sendAck",\
#                    "type"      : 3,\
#                    "code"      : 2\
#                }\
            ]\
        },\
        {\
            "category"  : "content",\
            "parameters":[\
                {\
                    "resource" : "/index.html",\
                    "http-status": "200 OK",\
                    "headers" : "Server: john.com\r\nDate: 2016-12-22 17:55\r\n\r\n",\
                    "body" : "Example of correct HTTP response"\
                },\
                {\
                    "resource" : "/404error.html",\
                    "http-status": "404 Not Found",\
                    "headers" : "Server: john.com\r\nDate: 2016-12-22 17:55\r\n\r\n",\
                    "body" : "Example of correct HTTP response"\
                }\
            ]\
        },\
        {\
            "category"  : "dns",\
            "parameters": [\
                {\
                    "q-addr" : "www.google.com",\
                    "response": "192.168.178.60"\
                },\
                {\
                    "q-addr" : "www.test.com",\
                    "response": "192.168.178.60"\
                }\
            ]\
        }\
    ]\
}

c = Connector(jconfig, debug=3)
c.run()


print "\n\n\n======= 8< ======== Config file ======== 8< ==========\n"
print json.dumps(jconfig, indent=2, sort_keys=False)
print "\n========= 8< ======== END Config file ========== 8< ==========\n"

