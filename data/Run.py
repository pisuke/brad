#script to run:
SCRIPT = "/Volumes/Data/Code/github/brad/src/brad.py"  
    
#path to your org.python.pydev.debug* folder (it may have different version number, in your configuration):
PYDEVD_PATH='/Applications/eclipse/plugins/org.python.pydev_2.7.5.2013052819/pysrc'

import pydev_debug as pydev

pydev.debug(SCRIPT, PYDEVD_PATH)
