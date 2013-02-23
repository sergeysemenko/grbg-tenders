# -*- coding: utf-8 -*-
import cgi
import datetime
import urllib2
import webapp2
import logging
import unicodedata
from google.appengine.ext import db
from google.appengine.api import taskqueue
from google.appengine.api import users
from google.appengine.api import memcache
from time import mktime
from google.appengine.api import urlfetch
import HTMLParser
import urllib2

#import feedparser

import jinja2
import os

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))




def get_content(url):
	opener = urllib2.build_opener()
	opener.addheaders = [('User-agent', 'Mozilla/5.0'), ("Accept-Encoding", 'UTF-8')]
	response = opener.open(url)
	return response.read()

def is_cyrillic(word):
	for c in word:
		if 'CYRILLIC' not in unicodedata.name(c):
			return False
	return True
	
def is_latin(word):
	for c in word:
		if 'LATIN' not in unicodedata.name(c):
			return False
	return True

def is_latin_cyrillic(word):
	for c in word:
		if 'LATIN' not in unicodedata.name(c) and 'CYRILLIC' not in unicodedata.name(c):
			return False
	return True

def is_interleaved(word):
	return is_latin_cyrillic(word) and not is_cyrillic(word) and not is_latin(word)

def is_interleaved_body(body):
	for word in body.split():
		if is_interleaved(word):
			return word
	return None

def is_cyrillic_char(c):
	return 'CYRILLIC' in unicodedata.name(c)
	
def is_latin_char(c):
	return 'LATIN' in unicodedata.name(c)

def decorate(word):
	res = ''
	for c in word:
		if is_latin_char(c):
			c = '<font color="red">%s</font>' % c
		res += c
	return res

def decorate_body(body):
	
	res = []
	for word in body.split():
		if is_interleaved(word):
			word = decorate(word)
		res.append(word.encode('utf-8'))
	return " ".join(res)
	


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
		dec = decorate_body(self.desc)
		return dec.decode('utf-8')

rss_url = "http://zakupki.gov.ru/223/purchase/public/notice-search-rss.html?"
static_params = "okvedText=&searchWord=&organName=&organName=&organName=&okdpText=&purchase=&activeTab=0&okdpId=&d-3771889-p=5&purchaseStages=APPLICATION_FILING&purchaseStages=COMMISSION_ACTIVITIES&purchaseStages=PLACEMENT_COMPLETE&fullTextSearchType=INFOS_AND_DOCUMENTS&customerOrgName=&customerOrgId=&customerOrgId=&purchaseMethodName=%3C%D0%92%D1%81%D0%B5%20%D1%81%D0%BF%D0%BE%D1%81%D0%BE%D0%B1%D1%8B%3E&okvedCode=&purchaseMethodId=&startingContractPriceFrom=&publishDateTo=&okdpCode=&publishDateFrom=21.02.2013&contractName=&startingContractPriceTo=&_purchaseStages=on&_purchaseStages=on&_purchaseStages=on&_purchaseStages=on&okvedId="

price_params_tmpl = '&startingContractPriceTo=%s&startingContractPriceFrom=%s&'
date_params_tmpl = '&publishDateFrom=%s&publishDateTo=%s&'

# there is for sure less than 200 entries after price_tail	
price_tail = 6100000

rss_desc_tag = u'Наименование закупки:'

def decode_rss_content(content, tag):
	"""
	@param content: content:encoded part of the rss item, raw string
	@param tag: the tag in the content:encoded part like Наименование закупки:,
				unicode() object
	"""
	h = HTMLParser.HTMLParser()
	content = content.encode('utf-8')
	tender = content.split(tag.encode('utf-8'))[1]
	tender = h.unescape(tender.decode('utf-8')).encode('utf-8')
	tender = tender.split('>')[1]
	tender = tender.split('<')[0]
	return tender

class ParsedRSSEntry:
	def __init__(self, edict):
		"""
		@param edict: {'link' : raw_str, 'content:encoded' : raw_str, 'pubDate' : raw_str}
					  generated by parse_rss_chunk()
		"""
		self.link = edict['link'].encode('utf-8')
		self.desc = decode_rss_content(edict['content:encoded'], rss_desc_tag)
		self.published = edict['pubDate'].encode('utf-8')
		self.published_parsed = datetime.datetime.strptime(self.published, 
												  '%a, %d %b %Y %H:%M:%S %Z')
	
	def __str__(self):
		return 'link: %s\n desc:%s\n published:%s\n published_parsed:%s' % (self.link, 
			self.desc, self.published, self.published_parsed)
	
	
	def get_or_insert(self, key):
		return RSSEntry.get_or_insert(key, url=self.link.decode('utf-8'), 
									  desc=self.desc.decode('utf-8'), 
									  date=self.published_parsed)

def keyname_from_link(link):
	pcs = link.split('purchaseId=')
	id = pcs[1].split('&')[0]
	return str(int(id))

def parse_tag_chunk(tag, text):
	"""
	@param tag: raw_str, xml tag like link or pubDate
	@param text: raw_str, text to search tag 
	
	@return tag_value: raw_str, content of tag (xmlNode.text)
	"""
	chunks = text.split('<%s>' % tag)
	val = chunks[1].split('</%s>' % tag)[0]
	return val
	

def parse_rss_chunk(chunk):
	"""
	@param chunk: raw_str, everything between <item> tags in rss stream
	
	@return edict: {'link' : raw_str, 'content:encoded' : raw_str, 'pubDate' : raw_str}
	"""
	entry = {'link' : None, 'content:encoded' : None, 'pubDate' : None}
	for tag in entry.keys():
		if tag in chunk:
			try:
				val = parse_tag_chunk(tag, chunk)
			except:
				logging.info('PARSE_RSS_CHUNK_ERROR: tag%s \nchunk:%s' % (tag, chunk))
				return None
			entry[tag] = val
	return entry

def fetch_rss_by_range2(datestr, end, start):
	"""
	@param datestr: raw_str, dd.mm.yyyy
	@param end: raw_str or int, upper price bound of tenders to fetch
	@param start: raw_str or int, lower price bound of tenders to fetch
	
	@return list( ParsedRSSEntry ): rss items received from rss request
	"""
	price_params = price_params_tmpl % (end, start)
	date_params = date_params_tmpl % (datestr, datestr)
	myurl = rss_url + price_params + date_params + static_params
	content = get_content(myurl)
	chunks = content.decode('utf-8').split('item')
	entries = []
	for chunk in chunks:
		if 'pubDate' in chunk:
			edict = parse_rss_chunk(chunk)
			if edict:	
				entry = ParsedRSSEntry(edict)
				entries.append(entry)
	return entries

def day_date(date):
	return datetime.datetime(year=date.year, month=date.month, day=date.day)		


def fetch_key(id):
	return 'batch_fetch_key_%s' % id

class FetchRSSBatch(webapp2.RequestHandler):
		
		
	def post(self):
		datestr = self.request.get('date')
		start = self.request.get('start')
		end = self.request.get('end')
		msg = 'FRSSBATCH: date %s, start %s, end%s' % (datestr, start, end)
		logging.info(msg)
		entries = fetch_rss_by_range2(datestr, end, start)
		logging.info("start %s, end%s fetched %d" % (start, end,len(entries)))
		for entry in entries:
			id = keyname_from_link(entry.link.decode('utf-8'))
			val = memcache.get(fetch_key(id))
			if val == None:
				entry.get_or_insert(id)
			#logging.info('INDEXING %s in place' % id)
			b = is_interleaved_body(entry.desc.decode('utf-8'))
			if b:
				logging.info('bad : %s' % b)
				bad = RSSBadEntry.get_or_insert(id, 
												url=entry.link.decode('utf-8'), 
												desc=entry.desc.decode('utf-8'), 
												bad=b, 
												date=entry.published_parsed)
		#db.put(entries)
		#self.redirect('/')
		
        

		
backwards_date = 'backwards'
def get_prev_back_date():
	q = IndexedDate.all()
	q.order('date')
	dates = list(q)
	logging.info("back date is %s"  % dates[0].date)
	return dates[0].date - datetime.timedelta(days=1)

class FetchRSS(webapp2.RequestHandler):
	def fetch(self, datestr):
		logging.info('FETCHING RSS FOR DATE %s' % datestr)
		range = 49999
		bigrange = range*5
		start = 0
		toohigh = 1000000
		while start < price_tail:
			cur_range = range
			if start > toohigh:
				cur_range = bigrange
			
			params = {
				'date' : datestr,
				'end'  : start + cur_range,
				'start': start 
			}
			taskqueue.add(url='/admin_fetch_rss_batch', params=params)
			start +=  cur_range +10
			
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
		IndexedDate.get_or_insert(keyname, date=date)
		self.redirect('/admin_')


import xml.dom.minidom
from xml.dom.minidom import Node


class ClearRSSIndex(webapp2.RequestHandler):
	def get(self):
		query = RSSBadEntry.all()
		query.order('url')
		entries = list(query)
		logging.info('clear: deleting %d bad entries' % len(entries))
		db.delete(entries)
		self.redirect('/')

class RSSEntryPrinter(webapp2.RequestHandler):
	def get(self):
		query = RSSEntry.all()
		query.order('url')
		entries = list(query)
		
		count = len(entries)
		
		template_values = {
			'count' : count,
			'entries'	: entries,
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
		key = bad_entries_mc_key(date, offset)
		logging.info('key %s' % key)
		entries = memcache.get('%s' % key)
		if entries is not None:
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
			query = db.GqlQuery('SELECT * FROM RSSBadEntry WHERE date >= :1 AND date <= :2 ORDER BY date DESC',
					date, end)
		else:
			query = query = db.GqlQuery('SELECT * FROM RSSBadEntry ORDER BY date DESC')

		entries = self.retreive_with_offset(query, offset)
		pages = self.gen_pages(offset, len(entries))
		entries = entries[0:printer_limit]
				
		template_values = {
			'num_links' 			: len(entries),
			'entries'				: entries,
			'enumerated_entries'	: enumerate(entries),
			'pages'       			: pages,
		} 
		
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
		self.render_page(entries)

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
		query = db.GqlQuery('SELECT * FROM RSSEntry WHERE date >= :1 AND date <= :2',
                date, end)
		entries = list(query)
		logging.info('start indexing %d entries' % len(entries))
		for entry in entries:
			b = is_interleaved_body(entry.desc)
			if b:
				logging.info('bad : %s' % b)
				keyname = keyname_from_link(entry.url)
				bad = RSSBadEntry.get_or_insert(keyname, url=entry.url, desc=entry.desc, bad=b, date=entry.date)
		memcache.flush_all()
		keyname = str(date)
		IndexedDate.get_or_insert(keyname, date=date)
		

class AddIndexeddate(webapp2.RequestHandler):
	def get(self):
		date = self.request.get('date')
		try:
			date = datetime.datetime.strptime(date, '%d.%m.%Y')
		except:
			logging.warning('bad date in request, assuming current')
			date = day_date(datetime.datetime.now())
				
		keyname = str(date)
		IndexedDate.get_or_insert(keyname, date=date)
		self.redirect('/admin_')
	
	def post(self):
		date = self.request.get('date')
		try:
			date = datetime.datetime.strptime(date, '%d.%m.%Y')
		except:
			logging.warning('bad date in request, assuming current')
			date = day_date(datetime.datetime.now())
				
		keyname = str(date)
		IndexedDate(date=date).put()
		

class TestCron(webapp2.RequestHandler):
	def get(self):
		date = datetime.datetime.now()
		logging.info('CRON JOB: date %s' % date)
		
from google.appengine.api import mail
from google.appengine.api import app_identity

class MsgHandler(webapp2.RequestHandler):
	def post(self):
		user = users.get_current_user()
		if user is None:
			  login_url = users.create_login_url(self.request.path)
			  self.redirect(login_url)
			  return
		
		content = self.request.get('message')
		template = jinja_environment.get_template('mail.html')
		escaped = template.render({'content': content})
		
		appid = app_identity.get_application_id()
		subject = 'Contact message received at %s' % appid
		
		mail.send_mail_to_admins(user.nickname(), subject, escaped, {})
		self.redirect('/')
		

app = webapp2.WSGIApplication([('/', MainPage),
							   ('/admin_rss_entry', RSSEntryPrinter),
							   ('/admin_', AdminPage),
							   ('/bad', BadRSSPrinter),
							   ('/msg', MsgHandler),
							   ('/admin_clear_rss_index', ClearRSSIndex),
                               ('/admin_index_rss_entries', IndexRSSEntries),
                               ('/admin_add_index_date', AddIndexeddate),
                               ('/admin_test_cron', TestCron),
                               ('/admin_fetch_rss', FetchRSS),
                               ('/admin_fetch_rss_batch',FetchRSSBatch)],
                              debug=True)
