#!/usr/bin/python
import sys
from lib.tcz import *
import json
import io

sys.path.append('.')
fileConfig = io.open(str(sys.argv[1]))
config = json.load(fileConfig)
c = Connector(config, debug=3)
c.run()


