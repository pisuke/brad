#script to run:
SCRIPT = "C:/Documents and Settings/<your profile>/workspace/<your script>.py"  
    
#path to your org.python.pydev.debug* folder (it may have different version number, in your configuration):
PYDEVD_PATH='C:/Program Files/Eclipse/plugins/org.python.pydev.debug_2.1.0.2011052613/pysrc'

import pydev_debug as pydev

pydev.debug(SCRIPT, PYDEVD_PATH)
