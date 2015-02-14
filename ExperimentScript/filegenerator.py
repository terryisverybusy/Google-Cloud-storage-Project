#!/usr/bin/env python

import itertools,subprocess
import sys
import random
import string
from time import gmtime, strftime

character = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
filecounts = [100, 100, 100, 100,  10,    1]
filesizes =  [1,   10,  100, 1024, 10240, 102400] # KB

sn = 0
testdir = "testfiles/"         #please make sure 'testfiles' folder is exist
for i in range(0, 6):          #6 types of files
    cnt = filecounts[i]
    sz = filesizes[i]
    print (cnt, sz,)

    nline = sz*1024/101         #compute the total number of lines
    for j in range(0, cnt):
        fname = testdir+str(sn)+".txt"    #set the file name
        sn = sn + 1
        print ("Writing", fname, "...")
        f = open(fname, "w")
        for k in range(0, nline):
            linecontent = string.join(random.sample(character, 10)).replace(" ","")
            for t in range(0, 9):                   #write the content of this line, 100 characters
                linecontent = linecontent + string.join(random.sample(character, 10)).replace(" ","")
            linecontent = linecontent + '\n'
            f.write(linecontent)        #write into the file


