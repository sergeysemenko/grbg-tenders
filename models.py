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
    price_start = db.IntegerProperty()
    price_end = db.IntegerProperty()
    
    @staticmethod
    def insert_unique(key, parsed_rss_entry):
        return RSSEntry.get_or_insert(
        	key, 
        	url=parsed_rss_entry.link.decode('utf-8'), 
            desc=parsed_rss_entry.desc.decode('utf-8'), 
            date=parsed_rss_entry.published_parsed,
            author=parsed_rss_entry.author,
            content=parsed_rss_entry.content,
            price_start=parsed_rss_entry.price_start,
            price_end=parsed_rss_entry.price_end)

    def update_from(self, **kwargs):
        self.url     = kwargs.get('url')
        self.desc    = kwargs.get('desc') 
        self.date    = kwargs.get('date')
        self.author  = kwargs.get('author')
        self.content = kwargs.get('content')
        self.price_start = kwargs.get('price_start')
        self.price_end   = kwargs.get('price_end')
    

class RSSBadEntry(RSSEntry):
    bad = db.StringProperty(required=True)
    desc_fixed = db.TextProperty()

    def update_from(self, **kwargs):
        super(RSSBadEntry, self).update_from(**kwargs)
        self.bad = kwargs.get('bad')
        self.desc_fixed = kwargs.get('desc_fixed')
    
    def decorated(self):
        dec = filters.decorate_body(self.desc)
        return dec.decode('utf-8')

    def fixed_decorated(self):
        if self.desc_fixed != None:
            dec = filters.decorate_body_all(self.desc_fixed)
        else:
            dec = 'WAS NOT FIXED YET'
        return dec.decode('utf-8')


def txn(EClass, key_name, **kwargs):
    entity = EClass.get_by_key_name(key_name)
    if entity is None:
        entity = EClass(key_name=key_name, **kwargs)
    else:
        entity.update_from(**kwargs)
    entity.put()
    return entity

def insert_or_update(EClass, key_name, **kwargs):
    return db.run_in_transaction(txn, EClass, key_name, **kwargs)





    
 





