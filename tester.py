from scapy.all import *
from lib.tcz import TCZee
from lib.tcz import HTTZee
from lib.tcz import Connector
from scapy.all import Automaton
from functools import wraps

import copy
import time


# To be used when working on local interface l0
#conf.L3socket = L3RawSocket
sys.path.append('.')

class Tester(object):
    
    def __init__(self, jsonDict={}):
        self.configRegistry=jsonDict
        # This is being added earlier as debug statement to check if the 
        # there is no change in the Automaton Flow. 
        # TCZee.graph()
    
    def runComponent(self):
        ''' Function which search for the list of json files in the specified 
        configuration folder and calls the jsonParse function in loops. This 
        is also part of Issue #5. '''
        for test_id, config in self.configRegistry.iteritems():

            if( config != {} and config['category']=='time' ):
                print "[time] Test started for %s"%(test_id)
                self.currentTest = Connector(config, debug=3)
                self.currentTest.run()
                print "[time] Test completed for %s"%(test_id)
            elif ( config != {} and config['category'] == 'content' ):
                print "[content] Test started for %s"%(test_id)
                self.currentTest = Connector(config, debug=3)
                self.currentTest.run()
                print "[content] Test completed for %s"%(test_id)
            elif ( config != {} and config['category'] == 'packet' ):
                print "[packet] Test started for %s"%(test_id)
                self.currentTest = Connector(config, debug=3)
                self.currentTest.run()
                print "[packet] Test completed for %s"%(test_id)
            else:
                print "JSON Config file empty or no valid test category."
            

class ConfigExpert(object):
    
    def __init__(self):
        self.jsonRegistry={}
        self.jsonCopy={}

    def process(self, rawJson):
        ''' Here the raw Json data from the file is process to 
        create a nested json with the test id as the keys for the
        jsonRegistry'''
        
        self.jsonCopy = copy.deepcopy(rawJson)
        current_key=self.jsonCopy['testID']
        self.jsonRegistry[current_key]={}
        del self.jsonCopy['testID']
        self.jsonRegistry[current_key]=self.jsonCopy

        # TODO: the logic for the combining the multi-config file
        # for the same testID must be handled here.
        
    
    def getRegistry(self):
        return self.jsonRegistry
    
