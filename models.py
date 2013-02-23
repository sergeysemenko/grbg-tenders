from google.appengine.ext import db
import filters

class IndexedDate(db.Model):
    date = db.DateTimeProperty(required=True)
    
    def __str__():
        return str(date)

class RSSEntry(db.Model):
    url = db.StringProperty(required=True)
    desc = db.TextProperty(required=True)
    date = db.DateTimeProperty(required=True)
    

class RSSBadEntry(RSSEntry):
    bad = db.StringProperty(required=True)
    
    def decorated(self):
        dec = filters.decorate_body(self.desc)
        return dec.decode('utf-8')