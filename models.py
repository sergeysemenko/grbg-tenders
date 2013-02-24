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
    
    @staticmethod
    def insert_unique(key, parsed_rss_entry):
        return RSSEntry.get_or_insert(
        	key, 
        	url=parsed_rss_entry.link.decode('utf-8'), 
            desc=parsed_rss_entry.desc.decode('utf-8'), 
            date=parsed_rss_entry.published_parsed)
    

class RSSBadEntry(RSSEntry):
    bad = db.StringProperty(required=True)
    
    def decorated(self):
        dec = filters.decorate_body(self.desc)
        return dec.decode('utf-8')