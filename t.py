#!/usr/bin/python

import json
from scapy.all import *
import sys
sys.path.append('.')
from libs.connector import Connector

log_interactive.setLevel(1)

jconfig = {\
    "test-id"  : "content001",\
    "interface": "eth0",\
    "lis-port" : 80,\
    "category" : "content",\
    "parameter": [\
        {\
            "resource" : "/index.html",\
            "http-status": "HTTP/1.1 200 OK\r\n",\
            "headers" : "Server: john.com\r\nDate: 2016-12-22 17:55\r\n\r\n",\
            "body" : "Example of correct HTTP response"\
        },\
        {\
            "resource" : "/404error.html",\
            "http-status": "HTTP/1.1 404 Resource not found\r\n",\
            "headers" : "Server: john.com\r\nDate: 2016-12-22 17:55\r\n\r\n",\
            "body" : "Example of body for 404 error"\
        }\
    ]\
}



c = Connector(jconfig, debug=3)
c.run()


print "\n\n\n======= 8< ======== Config file ======== 8< ==========\n"
print json.dumps(jconfig, indent=2, sort_keys=False)
print "\n========= 8< ======== END Config file ========== 8< ==========\n"

