#!/usr/bin/env python

from sys import argv
from os.path import splitext
from os import system

if len(argv)>1:
	items = argv[1:]
	for item in items:
		name = splitext(item)[0]
		if splitext(item)[1].lower()=='.obj':
			#print(item)
			cmd = 'obj2rad %s > %s.rad'  % (item,name)
			print(cmd)
			system(cmd)
			
