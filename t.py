#!/usr/bin/python

import json
from scapy.all import *
import sys
sys.path.append('.')
from lib.connector import Connector

log_interactive.setLevel(1)

jconfig = {
    "testID" : "Packet001",
    "category" : "packet",
#    "state"    : "BEGIN",
    "state" : "ESTABLISHED",
    "action" :"sendAck",
#    "action" : "BEGIN",
    "parameter" : "RP",
    "listeningPort" : 80,
    "listeningAddress" : "testing.com",
    "listeningInterface" : "eth0"
}




c = Connector(jconfig, debug=3)
c.run()


print "\n\n\n======= 8< ======== Config file ======== 8< ==========\n"
print json.dumps(jconfig, indent=2, sort_keys=False)
print "\n========= 8< ======== END Config file ========== 8< ==========\n"

