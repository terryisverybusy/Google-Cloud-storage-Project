import os
import urllib
import webapp2
import math

from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import memcache
from google.appengine.api import files
from decimal import *


try:
    files.gs
except AttributeError:
    import gs
    files.gs = gs

#this is the global variable to record the size of the cache and storage
cachemb = 0
storagemb = 0
#varial record the 100KB
BIGFILEBASE = 100*1024
#bucket path on GCS
BUCKET_PATH = '/gs/syssys'
#the is the controller of the memecache
ENABLEMEMCACHE = True

#to define the Filekey class, using the db.model, it is the key in memcache and GCS
class FileKey(db.Model):
  # the blob info key
  blobinfokey = db.StringProperty()
  # the location of the file: "memcache" or "cloudstorage"
  filelocation = db.StringProperty()
  #the data size
  datasize = db.IntegerProperty()


def filelist_key():
  return  db.Key.from_path('Filelist', 'default_filelist')


#the main handler, include javascript and HTML and some actions
class MainHandler(webapp2.RequestHandler):
  def get(self):
    #create the upload url
    upload_url = blobstore.create_upload_url('/upload')
    #HTML define
    self.response.out.write('<html>')
    self.response.out.write('<head>')
    self.response.out.write('<style>')
    self.response.out.write('body {background-color:SkyBlue }')
    self.response.out.write('h1   {color:yellow}')
    self.response.out.write('h3   {color:black}')
    self.response.out.write('h4   {color:green}')
    self.response.out.write('</style>')

    #define the javascript let the page to auto refresh once
    self.response.out.write("""
            <SCRIPT LANGUAGE="JavaScript">
                  String.prototype.queryString= function(name)
                   {
	                   var reg=new RegExp("[\?\&]" + name+ "=([^\&]+)","i"),r = this.match(reg);
	                   return r!==null?unescape(r[1]):null;
                   };
                window.onload=function(){
                var last=location.href.queryString("_v");
                document.body.innerHTML+=last||"";
               if(location.href.indexOf("?")==-1){
            location.href=location.href+"?_v="+(new Date().getTime());
                }else{
            var now=new Date().getTime();
            if(!last){
                location.href=location.href+"&_v="+(new Date().getTime());
            }else if(parseInt(last)<(now-1000)){
                location.href=location.href.replace("_v="+last,"_v="+(new Date().getTime()));
            }
        }
            };


               </SCRIPT>

                """)


    self.response.out.write('</head>')
    self.response.out.write('<body>')
    self.response.out.write("<h3>Coding by :</h3>")
    self.response.out.write("<h3>Zhaoan Guan   </h3>")
    
  




    #following are the HTML
    # insert
    self.response.out.write("<h4>insert</h4>")
    self.response.out.write('<form action="%s" method="POST" enctype="multipart/form-data">' % upload_url)
    self.response.out.write('File Key:<input type="text" name="filekey">')
    self.response.out.write("""Upload File: <input type="file" name="file"><br> <input type="submit"
        name="submit" value="Submit"> </form>""")

    # check
    self.response.out.write("<h4>Check</h4>")
    self.response.out.write("""
          <hr>
          <form action="/check" method="post">
            <div>File Key:<input type="text" name="filekey"></div>
            <div><input type="submit" value="Check This File Key"></div>
          </form>
          <hr>""")
    # delete
    self.response.out.write("<h4>remove</h4>")
    self.response.out.write("""
          <hr>
          <form action="/remove" method="post">
            <div>File Key:<input type="text" name="filekey"></div>
            <div><input type="submit" value="Remove"></div>
          </form>
          <hr>""")
    # Download
    self.response.out.write("<h4>find</h4>")
    self.response.out.write("""
          <hr>
          <form action="/download" method="post">
            <div>File Key:<input type="text" name="filekey"></div>
            <div><input type="submit" value="Find/Download"></div>
          </form>
          <hr>""")
    # List
    self.response.out.write("<h4>list</h4>")
    self.response.out.write("""<a href="/list">List</a>""")

    # Extra Credit
    self.response.out.write("<h1>This is the Extra Credit Part</h1>")
    # Check
    self.response.out.write("<h4>check cloud storage</h4>")
    self.response.out.write("""
          <hr>
          <form action="/checkcloudstorage" method="post">
            <div>File Key:<input type="text" name="filekey"></div>
            <div><input type="submit" value="Check This File Key"></div>
          </form>
          <hr>""")

    # checkCache
    self.response.out.write("<h4>checkCache</h4>")
    self.response.out.write("""
          <hr>
          <form action="/checkcache" method="post">
            <div>File Key:<input type="text" name="filekey"></div>
            <div><input type="submit" value="Check if This File Key is in Cache"></div>
          </form>
          <hr>""")
    # removeAllCache
    self.response.out.write("<h4>removeAllCache</h4>")
    self.response.out.write("""
          <hr>
          <form action="/removeallcache" method="post"
            <div><input type="submit" value="Remove All Cache"></div>
          </form>
          <hr>""")

    # removeAll
    self.response.out.write("<h4>RemoveAll</h4>")
    self.response.out.write("""
          <hr>
          <form action="/removeall" method="post"
            <div><input type="submit" value="Remove All"></div>
          </form>
          <hr>""")


	 # CacheSizeMB
    self.response.out.write("<h4>CacheSizeMB</h4>")
    self.response.out.write("""
          <hr>
          <form action="/cachesizemb" method="post"
            <div><input type="submit" value="CacheSizeMB(the total space (in MB) allocated to files in the cache of distributed storage system)"></div>
          </form>
          <hr>""")




    # CacheSizeElem
    self.response.out.write("<h4>CacheSizeElem</h4>")
    self.response.out.write("""
          <hr>
          <form action="/cachesizeelem" method="post"
            <div><input type="submit" value="CacheSizeElem(number of files in cache)"></div>
          </form>
          <hr>""")

     # StorageSizeMB
    self.response.out.write("<h4>StorageSizeMB</h4>")
    self.response.out.write("""
          <hr>
          <form action="/storagesizemb" method="post"
            <div><input type="submit" value="StorageSizeMB(the total space (in MB) allocated to files in the distributed storage system)"></div>
          </form>
          <hr>""")




    # StorageSizeElem
    self.response.out.write("<h4>StorageSizeElem</h4>")
    self.response.out.write("""
          <hr>
          <form action="/storagesizeelem" method="post"
            <div><input type="submit" value="StorageSizeElem(number of files in cloud storage)"></div>
          </form>
          <hr>""")

    # Find in File
    self.response.out.write("<h4>FindInFile</h4>")
    self.response.out.write("""
          <hr>
          <form action="/findinfile" method="post">
            <div>File Key:<input type="text" name="filekey"></div>
            <div>Expression:<input type="text" name="regexp"></div>
            <div><input type="submit" value="Check This File Key"></div>
          </form>
          <hr>""")

    # Listing
    self.response.out.write("<h4>Listing</h4>")
    self.response.out.write("""
          <hr>
          <form action="/listing" method="post">
            <div>Expression:<input type="text" name="regexp"></div>
            <div><input type="submit" value="List all files with expression"></div>
          </form>
          <hr>""")

    self.response.out.write('</body></html>')


#the handler for the insert action
class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
  def post(self):
    #to use the global cachemb and storagemb
    global cachemb
    global storagemb

    # save the file key and blobinfokey to Datastore
    mykey = self.request.get("filekey")
    filekey = FileKey(key_name =mykey, parent=filelist_key())

    #print out the key
    self.response.out.write("This is the File key:")
    self.response.out.write(filekey.key().id_or_name())
    self.response.out.write("</br>     </br>")


    # upload the file, 'file' is file upload field in the form
    upload_files = self.get_uploads('file')
    blob_info = upload_files[0]
    filekey.blobinfokey = str(blob_info.key())
    #print out the information
    self.response.out.write("</br>This is the Blob info key:")
    self.response.out.write(blob_info.key())
    self.response.out.write("</br>     </br>")
    self.response.out.write("</br>This is the Blob info size:")
    self.response.out.write(blob_info.size)
    self.response.out.write("</br>     </br>")
    #record the size of the file
    filekey.datasize = blob_info.size

    # An insert on a file that already exists will simply overwrite the entire contents of the file
    nowkeys = FileKey.all()
    nowkeys.filter('__key__ =', db.Key.from_path("FileKey", filekey.key().id_or_name(), parent=filelist_key()))
    if nowkeys.count() == 0:
      self.response.out.write("</br>This a a new file, no need to overwrite</br>")
    else:
      self.response.out.write("</br>This file already exist, we need to overwrite it</br>")
      for kkk in nowkeys:
          if kkk.datasize <= BIGFILEBASE:
              memcache.delete(kkk.key().id_or_name())
              files.delete(BUCKET_PATH+"/"+kkk.key().id_or_name())
              cachemb = cachemb - kkk.datasize
              storagemb = storagemb - kkk.datasize
          else:
              files.delete(BUCKET_PATH+"/"+kkk.key().id_or_name())
              storagemb = storagemb - kkk.datasize

    #To judge the file should be put into the memcache or nor
    if blob_info.size <= BIGFILEBASE and ENABLEMEMCACHE:
      # small file, put to memcache
      global cachemb
      cachemb += blob_info.size
      #add the file into the memcache
      memcache.add(mykey, blob_info)
      #set the location property
      filekey.filelocation = "memcache"
      #update the storage size
      global storagemb
      storagemb += blob_info.size
      # use filekey key name as the obj name in bucket
      write_path = files.gs.create(BUCKET_PATH+"/"+filekey.key().id_or_name(), mime_type='text/plain',
                                     acl='public-read')
      # Write to the file.
      with files.open(write_path, 'a') as fp:
        rstart = 0
        fsize = blob_info.size
        fetchsize = blobstore.MAX_BLOB_FETCH_SIZE - 1
        while rstart < fsize:
          fp.write( blobstore.fetch_data(blob_info, rstart, rstart+fetchsize))
          rstart = rstart + fetchsize
      # Finalize the file so it is readable in Google Cloud Storage.
      files.finalize(write_path)
      filekey.filelocation = "memcache"
      self.response.out.write("</br> Congratulations, File saved to memcache and GCS Success</br>")
      self.response.out.write("</br>     </br>")
      self.response.out.write("If you want to go ahead, please go back to the MainPage by yourself")

    #situation that only need to storage in the GCS
    else:
      global storagemb
      storagemb += blob_info.size
      # use filekey key name as the obj name in bucket
      write_path = files.gs.create(BUCKET_PATH+"/"+filekey.key().id_or_name(), mime_type='text/plain',
                                     acl='public-read')
      # Write to the file.
      with files.open(write_path, 'a') as fp:
        rstart = 0
        fsize = blob_info.size
        fetchsize = blobstore.MAX_BLOB_FETCH_SIZE - 1
        while rstart < fsize:
          fp.write( blobstore.fetch_data(blob_info, rstart, rstart+fetchsize))
          rstart = rstart + fetchsize
      # Finalize the file so it is readable in Google Cloud Storage.
      files.finalize(write_path)
      filekey.filelocation = "cloudstorage"
      self.response.out.write("</br> Congratulations,File saved to Google Cloud Storage Success.</br>")
      self.response.out.write("</br>     </br>")
      self.response.out.write("If you want to go ahead, please go back to the MainPage by yourself")
    #save the filekey or update in the db
    filekey.put()

#the handler for the list calss
class ListHandler(webapp2.RequestHandler):
  def get(self):
   #get all the keys
    filekeys = FileKey.all()
    self.response.out.write("<b>Following is the List</b>:</br>")
    for filekey in filekeys:
      self.response.out.write(filekey.key().id_or_name())
      self.response.out.write('</br>')

#the handler for the check class
class CheckHandler(webapp2.RequestHandler):
  def post(self):
    fkeystr = self.request.get("filekey")
    filekeys = FileKey.all()
    #get the keys that the name is the same with the parameter
    filekeys.filter('__key__ =', db.Key.from_path("FileKey", fkeystr, parent=filelist_key()))
    if filekeys.count() == 0:
      self.response.out.write("So sorry !!!!!!!!!!!!!!!!Key(%s) does NOT exists." % fkeystr)
    else:
      self.response.out.write("Congatulation !!!!!!!!!!!!  Key(%s) exists." % fkeystr)

#check the file exist in the cache or not
class CheckcacheHandler(webapp2.RequestHandler):
  def post(self):
    fkeystr = self.request.get("filekey")
    filekeys = FileKey.all()
    filekeys.filter('__key__ =',
      db.Key.from_path("FileKey", fkeystr, parent= filelist_key()))
    #use the filter the get the key of the files which exist in the memcache
    filekeys.filter('filelocation =', 'memcache')
    if filekeys.count() == 0:
      self.response.out.write("So sorry , Key(%s) does NOT exists in cache." % fkeystr)
    else:
      self.response.out.write("Congratulation !!!!!!!    Key(%s) exists in cache." % fkeystr)

#handler to chekc the file exist in the GCS or not
class CheckcloudstorageHandler(webapp2.RequestHandler):
  def post(self):
    fkeystr = self.request.get("filekey")
    filekeys = FileKey.all()
    filekeys.filter('__key__ =',
      db.Key.from_path("FileKey", fkeystr, parent= filelist_key()))
    #filekeys.filter('filelocation =', 'cloudstorage')
    if filekeys.count() == 0:
      self.response.out.write("Sorry , Key(%s) does NOT exists in distributed storage(Google Cloud Storage)." % fkeystr)
    else:
      self.response.out.write("Congratulation !!!!!!!!!Key(%s) exists in distributed storage(Google Cloud Storage)." % fkeystr)

#handler to remove all the cache
class removeallcacheHandler(webapp2.RequestHandler):
  def post(self):
    #update the global cachemb
    global cachemb
    cachemb = 0
    filekeys = FileKey.all()
    filekeys.filter('filelocation =', 'memcache')
    self.response.out.write("<b>Congratulation !!!!!!!Following files already Removed from cache</b>:</br>")
    for filekey in filekeys:
      self.response.out.write(filekey.key().id_or_name())
      #delete the file from the memcache
      memcache.delete(filekey.key().id_or_name())
      self.response.out.write('</br>')
      #update the location and update the db
      filekey.filelocation = "cloudstorage"
      db.put(filekey)

#handler for remove all
class removeallHandler(webapp2.RequestHandler):
  def post(self):
    global cachemb
    global storagemb
    #update the cacahemb and storagemb
    cachemb = 0
    storagemb = 0
    filekeys = FileKey.all()
    self.response.out.write("<b>Removed all</b>:</br>")
    for filekey in filekeys:
      self.response.out.write(filekey.key().id_or_name())
      if filekey.filelocation == "memcache":
        #delete from memcachae
        memcache.delete(filekey.key().id_or_name())
      else:
        #delete from GCS
        files.delete(BUCKET_PATH+"/"+str(filekey.key().id_or_name()))
      self.response.out.write('</br>')
        #udelete the key from the db
    for filekey in filekeys:
      db.delete(filekey.key())

#handler for the find handler
class DownloadHandler(blobstore_handlers.BlobstoreDownloadHandler):
  def post(self):
    fkeystr = self.request.get("filekey")
    filekeys = FileKey.all()
    filekeys.filter('__key__ =', db.Key.from_path("FileKey", fkeystr, parent=filelist_key()))
    if filekeys.count() == 0:
      self.response.out.write("So sorry , Key(%s) does NOT exists." % fkeystr)
    else:
      for ifile in filekeys:
        #check the cache first to improve the performance
        if ifile.filelocation == "memcache":
          #get content form the cache
          blob_info = memcache.get(ifile.key().id_or_name())
          self.send_blob(blob_info)
        else:
          #read the content from the GCS
          with files.open(BUCKET_PATH+"/"+ifile.key().id_or_name(), 'r') as fp:
            buf = fp.read(1000000)
            while buf:
                self.response.out.write(buf)
                buf = fp.read(1000000)
          self.response.out.write("From Google Cloud Storage file:" + ifile.key().id_or_name())

#the remove action at the basic credit part
class RemoveHandler(webapp2.RequestHandler):
  def post(self):
    global cachemb
    global storagemb
    #get the file key parameter
    fkeystr = self.request.get("filekey")
    filekeys = FileKey.all()
    #get the specific key
    thekey = db.Key.from_path("FileKey", fkeystr, parent=filelist_key())
    filekeys.filter('__key__ =', thekey)
    #the key not exist
    if filekeys.count() == 0:
      self.response.out.write("So sorry ,   Key(%s) does NOT exists." % fkeystr)
    #key exist
    else:
      f = db.get(thekey)
      if f.filelocation == "memcache":
        #update the cachemb and storagemb
        cachemb = cachemb - f.datasize
        storagemb = storagemb - f.datasize
        #delete from cache
        memcache.delete(f.key().id_or_name())
        #delete from GCS
        files.delete(BUCKET_PATH+"/"+f.key().id_or_name())
        self.response.out.write("Congratulations !!!!!!!!!Deleted from Memcache and GCS  Success</br>")
      #file exist in the GCS
      else:
        storagemb = storagemb - f.datasize
        #delete file from GCS
        files.delete(BUCKET_PATH+"/"+f.key().id_or_name())
        self.response.out.write("Congratulations !!!!!!!!!Deleted from Google Cloud Storage</br>")
      db.delete(thekey)
      self.response.out.write("Congratulations !!!!!!!!!Key(%s) removed." % fkeystr)


#the handler for the upload url
class UploadURLHandler(webapp2.RequestHandler):
  def get(self):
    upload_url = blobstore.create_upload_url('/upload')
    self.response.out.write(upload_url)


#handler to check the cachesize
class cachesizembHandler(blobstore_handlers.BlobstoreUploadHandler):
  def post(self):
      #read the global cachemb
       global cachemb
       #set the precise
       getcontext().prec = 30
       self.response.out.write("<b>Listen !!!!!!!!total space (in MB) allocated to files in the cache :  </b>: ")
       self.response.out.write(Decimal(cachemb)/Decimal(1048576))



#handler to chekc the cacheszie element
class cachesizeelemHandler(webapp2.RequestHandler):
  def post(self):
    filekeys = FileKey.all()
    #use the filter to get the number of files in the cache
    filekeys.filter('filelocation =', 'memcache')
    self.response.out.write("<b>Listen!!!!!!Now the Num of files in cache</b>: ")
    self.response.out.write(filekeys.count())


#handler for the total GCS  file size
class storagesizembHandler(blobstore_handlers.BlobstoreUploadHandler):
  def post(self):
       #read global storagemb
       global storagemb
       #set precise
       getcontext().prec = 30
       self.response.out.write("<b>Listen !!!!!!!!!total space (in MB) allocated to files in the GCS :  </b>: ")
       self.response.out.write(Decimal(storagemb)/Decimal(1048576))

#handler for the GCS files number
class storagesizeelemHandler(webapp2.RequestHandler):
  def post(self):
    filekeys = FileKey.all()
    self.response.out.write("<b>Listen !!!!!!!!!! Now the Num of files in cloud storage</b>: ")
    self.response.out.write(filekeys.count())

#then handler to searches for a regular expression in file key
class findinfileHandler(blobstore_handlers.BlobstoreDownloadHandler):
  def post(self):
    fkeystr = self.request.get("filekey")
    regexpstr = self.request.get("regexp")
    filekeys = FileKey.all()
    filekeys.filter('__key__ =', db.Key.from_path("FileKey", fkeystr, parent=filelist_key()))
    if filekeys.count() == 0:
      self.response.out.write("Key(%s) does NOT exists." % fkeystr)
    else:
      for ifile in filekeys:
        self.response.out.write("Matching contents:")
        if ifile.filelocation == "memcache":
          blob_info = memcache.get(ifile.key().id_or_name())
          blob_reader = blob_info.open()
          for line in blob_reader:
            if regexpstr in line:
              self.response.out.write(line)
        else:
          with files.open(BUCKET_PATH+"/"+ifile.key().id_or_name(), 'r') as fp:
            buf = fp.read(1000)
            while buf:
                if regexpstr in buf:
                  self.response.out.write(buf)
                buf = fp.read(1000000)

#fil names match the regular expression string
class ListingHandler(webapp2.RequestHandler):
  def post(self):
    filekeys = FileKey.all()
    regexpstr = self.request.get("regexp")
    self.response.out.write("<b>List with %s</b>:</br>" % regexpstr)
    for filekey in filekeys:
      if regexpstr in filekey.key().id_or_name():
        self.response.out.write(filekey.key().id_or_name())
        self.response.out.write('</br>')


app = webapp2.WSGIApplication([('/', MainHandler),
                               ('/upload', UploadHandler),
                               ('/uploadurl', UploadURLHandler),
                               ('/list', ListHandler),
                               ('/check', CheckHandler),
                               ('/download', DownloadHandler),
                               ('/remove', RemoveHandler),
                               ('/checkcache', CheckcacheHandler),
                               ('/removeallcache', removeallcacheHandler),
                               ('/removeall', removeallHandler),
                               ('/cachesizemb', cachesizembHandler),
                               ('/cachesizeelem', cachesizeelemHandler),
                               ('/storagesizemb', storagesizembHandler),
                               ('/storagesizeelem', storagesizeelemHandler),
                               ('/findinfile', findinfileHandler),
                               ('/listing', ListingHandler),
                               ('/checkcloudstorage', CheckcloudstorageHandler)],
                              debug=True)
