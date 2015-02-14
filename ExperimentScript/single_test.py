#!/usr/bin/env python

import threading
import time
import requests
import sys
from datetime import datetime
# appurl can be modified
appurl = "http://terry-1111.appspot.com/"
threadLock = threading.Lock()
last_filenum = -1
threads = []
nfiles = 411         #total number of test files

def insert(fkey, fpath):        #insert function
    """
    fkey is the key.
    fpath is the file path you want to upload
    return the running time of this operation
    """
    start_time = datetime.now()
    uploadurl = requests.get(appurl+"/uploadurl").text
    payload = {'filekey':fkey}
    files = {'file': open(fpath, 'r')}
    r = requests.post(uploadurl, data=payload, files=files)
    end_time = datetime.now()
    print >> sys.stderr, "Doing ", fkey
    return (end_time-start_time).total_seconds()

def check(fkey):              #check function
    start_time = datetime.now()
    payload = {'filekey':fkey}
    r = requests.post(appurl+"/check", data=payload)
    end_time = datetime.now()
    print >> sys.stderr, "Doing ", fkey
    return (end_time-start_time).total_seconds()

def find(fkey):             #find function
    start_time = datetime.now()
    payload = {'filekey':fkey}
    r = requests.post(appurl+"/download", data=payload)
    end_time = datetime.now()
    print >> sys.stderr, "Doing ", fkey
    return (end_time-start_time).total_seconds()

def remove(fkey):           #remove function
    start_time = datetime.now()
    payload = {'filekey':fkey}
    r = requests.post(appurl+"/remove", data=payload)
    end_time = datetime.now()
    print >> sys.stderr, "Doing ", fkey
    return (end_time-start_time).total_seconds()

def glist():                #list function
    start_time = datetime.now()
    r = requests.get(appurl+"/list")
    end_time = datetime.now()
    print >> sys.stderr, "Doing ", fkey
    return (end_time-start_time).total_seconds()

def filesizelist():
    filecounts = [100, 100, 100, 100,  10,    1]
    filesizes =  [1,   10,  100, 1024, 10240, 102400] # KB
    sizestore = []
    sn = 0
    for i in range(0, 6):
        cnt = filecounts[i]
        sz = filesizes[i]
        for j in range(0, cnt):
            sizestore.append(sz)
            sn = sn + 1
    return sizestore


# For multi threading
class myThread (threading.Thread):
    def __init__(self, threadID, operation):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.operation = operation
        self.perf = []
    def run(self):
        global last_filenum         #to guarantee threads not to use same files
        threadLock.acquire()
        my_filenum = last_filenum + 1
        last_filenum = my_filenum
        threadLock.release()
        #do the operations
        while my_filenum < nfiles:
            dur = 0
            if self.operation == "insert":
                dur = insert(str(my_filenum), 
                       "testfiles/"+str(my_filenum)+".txt")
            elif self.operation == "find":
                dur = find(str(my_filenum))
            elif self.operation == "remove":
                dur = remove(str(my_filenum))

            # time-duration, file-num
            self.perf.append( [ str(dur), str(my_filenum) ] ) 

            threadLock.acquire()           #lock the data
            my_filenum = last_filenum + 1
            last_filenum = my_filenum
            threadLock.release()            #after modify data, release the lock

if __name__ == '__main__':

    
    filesizes = filesizelist()
    
    if len(sys.argv) != 3:
        print "Usage: %s NumThreads Operations" % sys.argv[0]
        sys.exit(0)

    start_time = datetime.now()         #start time

    nthreads = int(sys.argv[1])
    operation = sys.argv[2]
    for threadid in range(0, nthreads):
        t = myThread(threadid, operation)
        t.start()                       #start thread
        threads.append(t)

    for t in threads:
        t.join()
    
    allperf = []
    for t in threads:
        allperf = allperf + t.perf      #put t.perf into allperf

    end_time = datetime.now()           #end time
    # nthreads operations totaltime
    totaltime = (end_time-start_time).total_seconds()
    print nthreads, operation, totaltime, "ALLOPERATIONS"

    for perf in allperf:
        # num-threads, operation, op-file-size, single-op-time, total-time
        opdur = perf[0]        
        fnumstr = perf[1]
        print nthreads, operation, filesizes[int(fnumstr)], opdur, totaltime, "SINGLEOPERATION"


