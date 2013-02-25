# -*- coding: utf-8 -*-
import cgi
import datetime
import urllib2
import webapp2
import logging
from google.appengine.ext import db
from google.appengine.api import taskqueue
from google.appengine.api import users
from google.appengine.api import memcache
from time import mktime
from google.appengine.api import urlfetch
import msearch

import rss
import core
import models
import filters

import jinja2
import os

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class AdminPage(webapp2.RequestHandler):
    def get(self):
        nickname = None
        user = users.get_current_user()
        user_id = None
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            nickname = user.nickname()
            user_id = user.user_id()
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
        
        template_values = {
            'id' : user_id,
            'url' : url,
            'nickname' : nickname,
            'user': user,
            'url_linktext': url_linktext,
        }
        
        template = jinja_environment.get_template('admin.html')
        self.response.out.write(template.render(template_values))

class FrontEnd(webapp2.RequestHandler):
    def render_header(self):
        nickname = None
        user = users.get_current_user()
        user_id = None
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            nickname = user.nickname()
            user_id = user.user_id()
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
        
        template_values = {
            'id' : user_id,
            'url' : url,
            'nickname' : nickname,
            'user': user,
            'url_linktext': url_linktext,
        }
        
        template = jinja_environment.get_template('boot2_header.html')
        return template.render(template_values)
    
    def render_footer(self):
        template = jinja_environment.get_template('boot2_footer.html')
        return template.render({})
        
    def render_page(self, body):
        header = self.render_header()
        footer = self.render_footer()
        self.response.out.write(header + body + footer )
        
class MainPage(FrontEnd):
    def get(self):
        template = jinja_environment.get_template('boot2_body.html')
        body = template.render({})
        self.render_page(body)

def day_date(date):
    return datetime.datetime(year=date.year, month=date.month, day=date.day)        


def fetch_key(id):
    return 'batch_fetch_key_%s' % id

rss_entry_index_name = 'RSSEntry_index'
rss_bad_entry_index_name = 'RSSBadEntry_index'

class FetchRSSBatch(webapp2.RequestHandler):
           
    def post(self):
        datestr = self.request.get('date')
        start = self.request.get('start')
        end = self.request.get('end')
        msg = 'FRSSBATCH: date %s, start %s, end%s' % (datestr, start, end)
        logging.info(msg)
        entries = rss.fetch_rss_by_range2(datestr, end, start)
        if len(entries) == rss.feed_max_size:
            logging.warning("FRSSBATCH_WARNING: reached feed size limit %d" %(
                rss.feed_max_size))
        logging.info("start %s, end%s fetched %d" % (start, end,len(entries)))
        for entry in entries:
            docid = rss.keyname_from_link(entry.link.decode('utf-8'))
            args = {
                    'url'     : entry.link.decode('utf-8'), 
                    'desc'    : entry.desc.decode('utf-8'), 
                    'date'    : entry.published_parsed,
                    'author'  : entry.author.decode('utf-8'),
                    'content' : entry.content.decode('utf-8'),
                    'price_start' : entry.price_start,
                    'price_end'   : entry.price_end
            }
            val = memcache.get(fetch_key(docid))
            if val == None:
                dbentry = models.insert_or_update(models.RSSEntry, docid, 
                    **args)
                # This is too expensive.. if we obtain enough search quota
                # maybe we can do that. Disabling for now.
                #msearch.index_entry(dbentry, docid, rss_entry_index_name)
            b = filters.scan(entry.desc.decode('utf-8'))
            if b:
                logging.info('bad : %s' % b)
                args['bad'] = b
                desc_fixed = filters.fix_body(entry.desc.decode('utf-8'))
                args['desc_fixed'] = desc_fixed
                bad = models.insert_or_update(
                    models.RSSBadEntry, 
                    docid, 
                    **args)
                msearch.index_entry(
                    bad, 
                    docid, 
                    rss_bad_entry_index_name, 
                    fixed=True)

        
backwards_date = 'backwards'
yesterday_date = 'yesterday'

def get_prev_back_date():
    q = models.IndexedDate.all()
    q.order('date')
    dates = list(q)
    if len(dates) == 0:
        date = datetime.datetime.now()
    else:
        date = dates[0].date
    logging.info("back date is %s"  % date)
    return dates[0].date - datetime.timedelta(days=1)

class FetchRSS(webapp2.RequestHandler):
    def fetch(self, datestr):
        logging.info('FETCHING RSS FOR DATE %s' % datestr)
        range = 50000
        bigrange = range*5
        start = 0
        toohigh = 1000000
        while start < rss.price_tail:
            cur_range = range
            if start > toohigh:
                cur_range = bigrange
            
            params = {
                'date' : datestr,
                'end'  : start + cur_range,
                'start': start 
            }
            taskqueue.add(url='/admin_fetch_rss_batch', params=params)
            start +=  cur_range + 1
            
        params = {
            'date' : datestr,
            'end'  : start + cur_range,
            'start': start 
        }
        taskqueue.add(url='/admin_fetch_rss_batch', params=params)
            
            
    def get(self):
        date = self.request.get('date')
        if date == backwards_date:
            date = get_prev_back_date()
            #don't index too much
            if date.year < 2013 and date.month < 9:
                return
        elif date == yesterday_date:
            #get the yesterday's date
            #this is for ensuring that we indexedeverything from yesterday
            logging.info('today is %s' % datetime.datetime.now())
            date = datetime.datetime.now() - datetime.timedelta(days=1)
            logging.info('indexing yesterday %s' % date)
            #datestr = '%s.%s.%s' % (date.day, date.month, date.year)
        else:
            try:
                date = datetime.datetime.strptime(date, '%d.%m.%Y')
            except:
                logging.warning('bad date in request, assuming current')
                date = day_date(datetime.datetime.now())
        datestr = "%s.%s.%s" % (date.day, date.month, date.year)
        self.fetch(datestr)
        memcache.flush_all()
        keyname = str(date)
        models.IndexedDate.get_or_insert(keyname, date=date)
        self.redirect('/admin_')


import xml.dom.minidom
from xml.dom.minidom import Node
import msearch

class ClearRSSIndex(webapp2.RequestHandler):
    def get(self):
        query = models.RSSBadEntry.all()
        query.order('url')
        entries = list(query)
        logging.info('clear: deleting %d bad entries' % len(entries))
        db.delete(entries)
        self.redirect('/')


class RSSEntryPrinter(webapp2.RequestHandler):
    def get(self):
        query = models.RSSEntry.all()
        query.order('url')
        entries = list(query)
        
        count = len(entries)
        
        template_values = {
            'count' : count,
            'entries'   : entries,
        } 
        template = jinja_environment.get_template('entry.html')
        self.response.out.write(template.render(template_values))


exptime = 3600*24

def parse_offset(offset):
    try:
        offset = int(offset)
    except:
        logging.info('bad offset, assuming 0')
        offset = 0
    return offset
    

def bad_entries_mc_key(date, offset=None):
    key = "bad_entries_"
    if date:
        key += '%02d%02d%04d' % (date.day, date.month, date.year)
    if offset:
        key += '_offset_%d' % offset
    return key

printer_limit = 10
retreive_limit = printer_limit * 3

class BadRSSPrinter(FrontEnd):
    
    def get_cursor_key(self, id):
        return 'BadRSSPrineter_cursor_key_%s'
    
    def get_cursor(self, id):
        key = self.get_cursor_key(id)
        cursor = memcache.get(key)
        return cursor
    
    def get_bad_entries(self, date, offset):
        debug = self.request.get('debug')
        key = bad_entries_mc_key(date, offset)
        logging.info('key %s' % key)
        entries = memcache.get('%s' % key)
        if entries is not None and not debug:
            logging.info('found key %s' % key)
            return entries
        else:
            entries = self.render_entries(date, offset)
            logging.info('missed key %s' % key)
            if not memcache.add(key, entries, time=exptime):
                logging.error('Memcache set failed.')
            return entries
    
    def retreive_with_offset(self, query, offset):
        #cursor can only implement "view-next-page" func without prev page
        #this is not convenient.
        #offset however just discards the entries, they are still retrieved
        #for now we are willing to pay 'offset' price
        #cursor = self.get_cursor()
        
        #retrive one limit more to know if we have links for next page
        entries = list(query.run(limit=retreive_limit, offset=offset))
        return entries
        
    def retreive_with_cursor(self, query, id):
        #cursor can only implement "view-next-page" func without prev page
        #this is not convenient.
        #offset however just discards the entries, they are still retrieved
        #for now we are willing to pay 'offset' price
        cursor = self.get_cursor(id)
        return list(query.run(limit=retreive_limit, start_cursor=cursor))
    
    def gen_pages(self, offset, num_links):
        idx = 0
        pages = []
        max_pages = 16
        if num_links == 0:
            return []
        for i in range(0, (offset + num_links) / printer_limit):
            pages.append((i * printer_limit, i))
        #if we have too much pages, hide first ones
        pages = pages[-max_pages:]
        #add pretty arrow
        if num_links == retreive_limit:
            pages[-1] = (pages[-1][0], '>')
        return pages
            
    def render_entries(self, date, offset):
        msg = ''
        if date:
            end = date + datetime.timedelta(days=1)
            logging.info('date start: %s' % date)
            logging.info('date end: %s' % end)
            query = db.GqlQuery(
                'SELECT * FROM RSSBadEntry '\
                'WHERE date >= :1 AND date <= :2 ORDER BY date DESC',
                date, end)
        else:
            query = query = db.GqlQuery(
                'SELECT * FROM RSSBadEntry ORDER BY date DESC')

        entries = self.retreive_with_offset(query, offset)
        pages = self.gen_pages(offset, len(entries))
        entries = entries[0:printer_limit]
                
        template_values = {
            'num_links'             : len(entries),
            'entries'               : entries,
            'enumerated_entries'    : enumerate(entries),
            'pages'                 : pages,
        } 

        debug = self.request.get('debug')
        if debug:
            logging.info('debug rendering')
            template_values['debug'] = True
        
        template = jinja_environment.get_template('boot2_bad.html')
        return template.render(template_values) 
            
    def get(self):
        date = self.request.get('date')
        logging.info('DATE %s' %date)
        try:
            date = datetime.datetime.strptime(date, '%d.%m.%Y')
        except:
            logging.info('bad date in request, assuming current')
            date = None
        offset = parse_offset(self.request.get('offset'))       
        entries = self.get_bad_entries(date, offset)
        template = jinja_environment.get_template('date_box.html')
        body = template.render({'search_results' : entries})
        self.render_page(body)

class IndexRSSEntries(webapp2.RequestHandler):

    def get(self):
        self.do_index()
        self.redirect('/admin_')
        
    def post(self):
        self.do_index()
        
    def do_index(self):
    
        date = self.request.get('date')
        if date == backwards_date:
            date = get_prev_back_date()
            #don't index too much
            if date.year < 2013 and date.month < 9:
                return
        else:
            try:
                date = datetime.datetime.strptime(date, '%d.%m.%Y')
            except:
                logging.warning('bad date in request, assuming current')
                date = day_date(datetime.datetime.now())
        logging.info('INDEXING WITH DATE %s' % date)
        end = date + datetime.timedelta(days=1)
        query = db.GqlQuery(
            'SELECT * FROM RSSEntry WHERE date >= :1 AND date <= :2',
                date, end)
        entries = list(query)
        logging.info('start indexing %d entries' % len(entries))
        for entry in entries:
            b = filters.scan(entry.desc)
            if b:
                logging.info('bad : %s' % b)
                keyname = rss.keyname_from_link(entry.url)
                bad = models.RSSBadEntry.get_or_insert(keyname, 
                    url=entry.url, desc=entry.desc, bad=b, date=entry.date)
        memcache.flush_all()
        keyname = str(date)
        models.IndexedDate.get_or_insert(keyname, date=date)
        

class AddIndexeddate(webapp2.RequestHandler):
    def get(self):
        date = self.request.get('date')
        try:
            date = datetime.datetime.strptime(date, '%d.%m.%Y')
        except:
            logging.warning('bad date in request, assuming current')
            date = day_date(datetime.datetime.now())
                
        keyname = str(date)
        models.IndexedDate.get_or_insert(keyname, date=date)
        self.redirect('/admin_')
    
    def post(self):
        date = self.request.get('date')
        try:
            date = datetime.datetime.strptime(date, '%d.%m.%Y')
        except:
            logging.warning('bad date in request, assuming current')
            date = day_date(datetime.datetime.now())
                
        keyname = str(date)
        models.IndexedDate(date=date).put()
        

class TestCron(webapp2.RequestHandler):
    def get(self):
        date = datetime.datetime.now()
        logging.info('CRON JOB: date %s' % date)
        
from google.appengine.api import mail
from google.appengine.api import app_identity

class MsgHandler(FrontEnd):
    def get(self):
        template = jinja_environment.get_template('contact.html')
        body = template.render({})
        self.render_page(body)
        
    def get_escaped(self, param):
        content = self.request.get(param)
        template = jinja_environment.get_template('mail.html')
        return template.render({'content': content})
        
    def post(self):
#       user = users.get_current_user()
#       if user is None:
#             login_url = users.create_login_url(self.request.path)
#             self.redirect(login_url)
#             return
        
        name = self.get_escaped('name')
        email = self.get_escaped('email')
        if not mail.is_email_valid(email):
            email = 'unknown@mail.com'
        message = self.get_escaped('message')
        
        appid = app_identity.get_application_id()
        subject = 'Contact message received at %s from %s' % (appid, name)
        
        try:
            mail.send_mail_to_admins(
                sender=email, subject=subject, body=message)
        except:
            logging.info("email failed with %s %s %s " %(name, email, message))
        self.redirect('/')


class IndexBadEntries(webapp2.RequestHandler):
    def get(self):
        limit = 500
        offset = 0
        query = db.GqlQuery(
                'SELECT * FROM RSSBadEntry ORDER BY date DESC')
        entries = list(query.run(limit=limit, offset=offset))
        logging.info('indexing %d entries' % len(entries))
        for entry in entries:
            msearch.index_entry(entry)
        self.redirect('/')

import HTMLParser

class ClearIndex(webapp2.RequestHandler):

    def clear(self, index_name):
        logging.info('received clear request for %s' % index_name)
        is_clear = msearch.clear_index(index_name, limit=100)
        if not is_clear:
            logging.info('%s needs more cleaning' % index_name)
            params = {'index_name': index_name}
            taskqueue.add(url='/admin_clear_index', params=params)
        else:
            logging.info('%s is clear! good job!' % index_name)

    def get(self):
        self.clear(rss_entry_index_name)
        #self.clear(rss_bad_entry_index_name)
        self.redirect('/admin_')

    def post(self):
        index_name = self.request.get('index_name')
        if index_name:
            self.clear(index_name) 
            
        else:
            logging.error('INDEX_CLEAR_ERROR no index name')

class SearchPrinter(FrontEnd):
    def render_search_results(self, query):
        logging.info('searching for query: %s' % query)
        logging.info('type q before: %s' % type(query))
        #datestr = self.request.get('date')
        #date = datetime.datetime.strptime(datestr, '%d.%m.%Y')

        # Disabled.
        # results = msearch.search_entries(query=query,
        #     index_name=rss_entry_index_name)

        hidden_results = msearch.search_entries(query=query,
            index_name=rss_bad_entry_index_name, hidden=True)
        
        if not hidden_results:
            template = jinja_environment.get_template('search_error.html')
            return template.render({})
        
        #count = len(results)

        #We will not search in regular entries since there are too
        #many of them and search quota is only
        #20,000/day and 250MB total index size
        # template_values = {
        #     'title'     : 'first 20 regular tenders',
        #     'count'     : len(results),
        #     'results'   : results,
        # }
        
        hidden_template_values = {
            'title'     : 'first 20 hidden tenders',
            'hidden'    : True,
            'count'     : len(hidden_results),
            'results'   : hidden_results,
        } 
        debug = self.request.get('debug')
        if debug:
            hidden_template_values['debug'] = True
        template = jinja_environment.get_template('search_results.html')
        #reg_res = template.render(template_values)
        hidden_res = template.render(hidden_template_values)
        return hidden_res

    def get(self):
        search_results = ''
        query = self.request.get('query')
        if query:
            search_results = self.render_search_results(query)
        template = jinja_environment.get_template('search_box.html')
        body = template.render({'search_results' : search_results})
        self.render_page(body)

             
        

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/admin_rss_entry', RSSEntryPrinter),
                               ('/admin_', AdminPage),
                               ('/bad', BadRSSPrinter),
                               ('/contact', MsgHandler),
                               #('/admin_clear_rss_index', ClearRSSIndex),
                               ('/admin_index_rss_entries', IndexRSSEntries),
                               ('/admin_add_index_date', AddIndexeddate),
                               ('/admin_test_cron', TestCron),
                               ('/admin_fetch_rss', FetchRSS),
                               ('/admin_fetch_rss_batch',FetchRSSBatch),
                               ('/admin_index', IndexBadEntries),
                               ('/admin_clear_index', ClearIndex),
                               ('/search', SearchPrinter)],
                              debug=True)
