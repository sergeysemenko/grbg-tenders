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
    author = db.TextProperty()
    content = db.TextProperty()
    
    @staticmethod
    def insert_unique(key, parsed_rss_entry):
        return RSSEntry.get_or_insert(
        	key, 
        	url=parsed_rss_entry.link.decode('utf-8'), 
            desc=parsed_rss_entry.desc.decode('utf-8'), 
            date=parsed_rss_entry.published_parsed,
            author=parsed_rss_entry.author,
            content=parsed_rss_entry.content)

    def update_from(self, **kwargs):
        self.url     = kwargs.get('url')
        self.desc    = kwargs.get('desc') 
        self.date    = kwargs.get('date')
        self.author  = kwargs.get('author')
        self.content = kwargs.get('content')
    

class RSSBadEntry(RSSEntry):
    bad = db.StringProperty(required=True)

    def update_from(self, **kwargs):
        super(RSSBadEntry, self).update_from(**kwargs)
        self.bad = kwargs.get('bad')
    
    def decorated(self):
        dec = filters.decorate_body(self.desc)
        return dec.decode('utf-8')


def txn(EClass, key_name, **kwargs):
    entity = EClass.get_by_key_name(key_name)
    if entity is None:
        entity = EClass(key_name=key_name, **kwargs)
    else:
        entity.update_from(**kwargs)
    entity.put()

def insert_or_update(EClass, key_name, **kwargs):
    return db.run_in_transaction(txn, EClass, key_name, **kwargs)





    
 





