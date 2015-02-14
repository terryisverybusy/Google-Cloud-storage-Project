#!/usr/bin/env python


import itertools,subprocess
import sys
from time import gmtime, strftime, sleep

nthreads = ["1","4"]            #1 thread and 4 threads
operations = ["insert", "find", "remove"]       #different operations

parameters = [nthreads, operations]

paralist = list(itertools.product(*parameters))    #the parameters for running single_test.py

jobid = strftime("%Y-%m-%d-%H-%M-%S", gmtime())
logname = jobid + ".log"
resultname = jobid + ".result"


if __name__ == '__main__':
    logf = open(logname, 'a')
    resultf = open(resultname, 'a')
    header = "nthreads operation time"
    resultf.write(header + "\n")
    print header

    for rep in range(0,2):          #do the different experiments
        for para in paralist:
            print para
            sys.stdout.flush()
            mycmd = "python single_test.py".split() + list(para)        #run another file single_test.py
            proc = subprocess.Popen(mycmd,
                           stdout=subprocess.PIPE)             #get the output from single_test.py
                           #stderr=logf)
            proc.wait()
            for line in proc.stdout:
                resultf.write( line ) 
                sys.stdout.flush()
            sleep(60) # sleep for a while for consistency.
    
    logf.close()
    resultf.close()
