#!/usr/bin/python

import json
from scapy.all import *
import sys
sys.path.append('.')
from libs.connector import Connector

log_interactive.setLevel(1)

jconfig = {\
    "test-id" : "delay-001", \
    "interface" : "eth0", \
    "lis-port" : 80, \
    "category" : "time", \
    "parameter" : [\
        {\
            "state" : "ESTABLISHED",\
            "action" : "sendAck",\
            "delay" : 0\
        },\
        {\
            "state" : "ESTABLISHED",\
            "action" : "send_finAck",\
            "delay" : 0\
        }\
    ]\
}
 




c = Connector(jconfig, debug=3)
c.run()


print "\n\n\n======= 8< ======== Config file ======== 8< ==========\n"
print json.dumps(jconfig, indent=2, sort_keys=False)
print "\n========= 8< ======== END Config file ========== 8< ==========\n"

