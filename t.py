#!/usr/bin/python

import json
from scapy.all import *
import sys
sys.path.append('.')
from libs.connector import Connector

log_interactive.setLevel(1)

jconfig = {
    "testID" : "Packet001",
    "category" :"packet",
        "state" : "ESTABLISHED",
    "action" :"sendAck",
    "parameter" : "RPA",
    "listeningPort" : 80,
    "listeningAddress" : "abc.com",
        "listeningInterface" : "eth0",
        "dnzLookUp" :   [
                {
                    "testing.com" : "192.168.2.1"
                },
                {
                    "google.com" : "192.168.2.21"
                }
            ]
}
 




c = Connector(jconfig, debug=3)
c.run()


print "\n\n\n======= 8< ======== Config file ======== 8< ==========\n"
print json.dumps(jconfig, indent=2, sort_keys=False)
print "\n========= 8< ======== END Config file ========== 8< ==========\n"

