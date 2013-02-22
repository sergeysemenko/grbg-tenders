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

#import feedparser

import jinja2
import os

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


# class Greeting(db.Model):
#   """Models an individual Guestbook entry with an author, content, and date."""
#   author = db.StringProperty()
#   content = db.StringProperty(multiline=True)
#   date = db.DateTimeProperty(auto_now_add=True)
# 
# 
# def guestbook_key(guestbook_name=None):
#   """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
#   return db.Key.from_path('Guestbook', guestbook_name or 'default_guestbook')

import urllib2

def get_content(url):
	opener = urllib2.build_opener()
	opener.addheaders = [('User-agent', 'Mozilla/5.0'), ("Accept-Encoding", 'UTF-8')]
	response = opener.open(url)
	return response.read()

def get_num_links(lines):
	num_mark = 'class="active"'
	for i,line in enumerate(lines):
		if num_mark in line:
			num_links = lines[i+2].strip().strip(')').split('(')[1]
			num_links = num_links.decode('utf-8')
			num_links = int(''.join(num_links.split()))
			return num_links
	return None

def get_links(lines):
	links = []
	mark = 'dropTop'
	for i,line in enumerate(lines):
		if mark in line:
			href = lines[i+2]
			link = href.split('"')[1]
			links.append(base_url + link)
	return links

def get_lines(url):
	opener = urllib2.build_opener()
	opener.addheaders = [('User-agent', 'Mozilla/5.0'), ("Accept-Encoding", 'UTF-8')]
	response = opener.open(url)
	return response.readlines()

myurl = 'http://zakupki.gov.ru/223/purchase/public/notification/search.html?purchase=&startingContractPriceFrom=&okvedCode=&okvedText=&customerOrgName=&searchWord=&startingContractPriceTo=&purchaseStages=APPLICATION_FILING&purchaseStages=COMMISSION_ACTIVITIES&purchaseStages=PLACEMENT_COMPLETE&customerOrgId=&customerOrgId=&okdpId=&purchaseMethodName=%3C%D0%92%D1%81%D0%B5+%D1%81%D0%BF%D0%BE%D1%81%D0%BE%D0%B1%D1%8B%3E&activeTab=0&okvedId=&okdpText=&okdpCode=&_purchaseStages=on&_purchaseStages=on&_purchaseStages=on&_purchaseStages=on&publishDateTo=&organName=&organName=&organName=&purchaseMethodId=&contractName=&fullTextSearchType=INFOS_AND_DOCUMENTS'
base_url = 'http://zakupki.gov.ru'

def get_order_str(lines, i):
	line = ''
	res = []
	# TODO: parse html properly
	while '</span>' not in line:
		i = i + 1
		line = lines[i].strip()
		if '<' not in line and line != '':
			res.append(line.strip())
	return "\n".join(res)

def get_order(url):
	lines = get_lines(url)
	mark = 'Наименование закупки'
	for i,line in enumerate(lines):
		if mark in line:
			return get_order_str(lines, i)

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
		#         guestbook_name=self.request.get('guestbook_name')
		#         greetings_query = Greeting.all().ancestor(
		#             guestbook_key(guestbook_name)).order('-date')
		#         greetings = greetings_query.fetch(10)
		
		template = jinja_environment.get_template('boot2_body.html')
		body = template.render({})
		self.render_page(body)

class OrderLink(db.Model):
    url = db.StringProperty(required=True)

class OrderSnippet(OrderLink):
    snippet = db.TextProperty(required=True)
    
class BadSnippet(OrderSnippet):
    bad = db.StringProperty(required=True)
    
    def decorated(self):
    	#return self.snippet#.decode('utf-8').encode('utf-8')
    	dec = decorate_body(self.snippet)
    	return dec.decode('utf-8')

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
	

url_tmpl = "http://zakupki.gov.ru/223/purchase/public/notification/search.html?publishDateFrom=20.02.2013&d-3771889-p=%s&purchase=%s&purchaseStages=APPLICATION_FILING&_purchaseStages=on&purchaseStages=COMMISSION_ACTIVITIES&_purchaseStages=on&_purchaseStages=on&purchaseStages=PLACEMENT_COMPLETE&_purchaseStages=on&organName=&fullTextSearchType=INFOS_AND_DOCUMENTS&activeTab=0"

init_url_tmpl = "http://zakupki.gov.ru/223/purchase/public/notification/search.html?publishDateFrom=20.02.2013&purchase=%s&purchaseStages=APPLICATION_FILING&_purchaseStages=on&purchaseStages=COMMISSION_ACTIVITIES&_purchaseStages=on&_purchaseStages=on&purchaseStages=PLACEMENT_COMPLETE&_purchaseStages=on&organName=&fullTextSearchType=INFOS_AND_DOCUMENTS&activeTab=0"
base_url = 'http://zakupki.gov.ru'


rss_url = "http://zakupki.gov.ru/223/purchase/public/notice-search-rss.html?"
static_params = "okvedText=&searchWord=&organName=&organName=&organName=&okdpText=&purchase=&activeTab=0&okdpId=&d-3771889-p=5&purchaseStages=APPLICATION_FILING&purchaseStages=COMMISSION_ACTIVITIES&purchaseStages=PLACEMENT_COMPLETE&fullTextSearchType=INFOS_AND_DOCUMENTS&customerOrgName=&customerOrgId=&customerOrgId=&purchaseMethodName=%3C%D0%92%D1%81%D0%B5%20%D1%81%D0%BF%D0%BE%D1%81%D0%BE%D0%B1%D1%8B%3E&okvedCode=&purchaseMethodId=&startingContractPriceFrom=&publishDateTo=&okdpCode=&publishDateFrom=21.02.2013&contractName=&startingContractPriceTo=&_purchaseStages=on&_purchaseStages=on&_purchaseStages=on&_purchaseStages=on&okvedId="

price_params_tmpl = '&startingContractPriceTo=%s&startingContractPriceFrom=%s&'
date_params_tmpl = '&publishDateFrom=%s&publishDateTo=%s&'

init_url = 'http://zakupki.gov.ru/223/purchase/public/notification/search.html?'


def add_rss_entries(cache, entries):
	for entry in entries:
		if entry.link not in cache:
			cache[entry.link] = entry

def fetch_rss_by_range(datestr, end, start):
	price_params = price_params_tmpl % (end, start)
	date_params = date_params_tmpl % (datestr, datestr)
	
	feedinput = urlfetch.fetch(rss_url + price_params + date_params + static_params)
	
	feed = feedparser.parse(feedinput.content)
	#feed = feedparser.parse( rss_url + price_params + date_params + static_params)
	return feed.entries

# there is for sure less than 200 entries after price_tail	
price_tail = 6100000

def fetch_rss(datestr):
	cache = {}
	date_params = date_params_tmpl % (datestr, datestr)
	lines = get_lines(init_url + date_params + static_params)
		
	num_links = get_num_links(lines)
	
	range = 100000
	bigrange = range*5
	start = 0
	end = start + range
	toohigh = 1000000
	zcount = 3
	maxz = 10
	while len(cache) < num_links:
		cur_range = range
		if start > toohigh:
			cur_range = bigrange
		entries = fetch_rss_by_range(datestr, start + cur_range, start)
		add_rss_entries(cache, entries)
		if len(entries) == 0:
			zcount += 1
			if zcount > maxz:
				break
		start +=  cur_range
	return cache

def parse_tag_chunk(tag, text):
	chunks = text.split('<%s>' % tag)
	val = chunks[1].split('</%s>' % tag)[0]
	return val
	

def parse_rss_chunk(chunk):
	entry = {'link' : None, 'content:encoded' : None, 'pubDate' : None}
	for tag in entry.keys():
		if tag in chunk:
			val = parse_tag_chunk(tag, chunk)
			entry[tag] = val
	return entry

def decode_rss_content(content):
	h = HTMLParser.HTMLParser()
	content = content.encode('utf-8')
	tender = content.split(u'Наименование закупки:'.encode('utf-8'))[1]
	tender = h.unescape(tender.decode('utf-8')).encode('utf-8')
	tender = tender.split('>')[1]
	tender = tender.split('<')[0]
	return tender

def get_desc_rss(entry):
	content = entry['content'][0]['value']
	return decode_rss_content(content)

class ParsedRSSEntry:
	def __init__(self, edict):
		self.link = edict['link'].encode('utf-8')
		self.desc = decode_rss_content(edict['content:encoded'])
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

def fetch_rss_by_range2(datestr, end, start):
	price_params = price_params_tmpl % (end, start)
	date_params = date_params_tmpl % (datestr, datestr)
	myurl = rss_url + price_params + date_params + static_params
	content = get_content(myurl)
	chunks = content.decode('utf-8').split('item')
	entries = []
	for chunk in chunks:
		if 'pubDate' in chunk:
			edict = parse_rss_chunk(chunk)
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
		self.redirect('/admin_')
		

class IndexHandler(webapp2.RequestHandler):
	def get(self):
		keyword = ''
		lines = get_lines(init_url_tmpl %  keyword)
		
		num_links = get_num_links(lines)
		num_pages = (num_links / 10) + (num_links % 10 != 0) 
		logging.info('indexhandler found %s pages for %s' % (num_pages, keyword)) 
		for page in range(1, num_pages+1):
			logging.info('indexhandler with page %s' % page)
			# Add the task to the default queue.
			taskqueue.add(url='/admin_fetch_addresses', params={'page': page})
		
		self.redirect('/')

class FetchHandler(webapp2.RequestHandler):
	def get(self):
		logging.info('fetchhandler started ')
		query = OrderLink.all()
		query.order('url')
		links = list(query)
		 
		for link in links:
			# Add the task to the default queue.
			keyname = "%s" % link.url
			logging.info('checking %s' % keyname)
			taskqueue.add(url='/admin_fetch_snippet', params={'page': link.url})
		
		self.redirect('/')

af_url = 'http://zakupki.gov.ru/223/purchase/public/notification/search.html?purchase=&startingContractPriceFrom=&okvedCode=&okvedText=&customerOrgName=&searchWord=&startingContractPriceTo=&purchaseStages=APPLICATION_FILING&purchaseStages=COMMISSION_ACTIVITIES&purchaseStages=PLACEMENT_COMPLETE&customerOrgId=&customerOrgId=&okdpId=&purchaseMethodName=%3C%D0%92%D1%81%D0%B5+%D1%81%D0%BF%D0%BE%D1%81%D0%BE%D0%B1%D1%8B%3E&activeTab=0&okvedId=&okdpText=&okdpCode=&_purchaseStages=on&_purchaseStages=on&_purchaseStages=on&_purchaseStages=on&publishDateTo=&organName=&organName=&organName=&purchaseMethodId=&contractName=&fullTextSearchType=INFOS_AND_DOCUMENTS'


class AddressFetcher(webapp2.RequestHandler):
	def post(self):
		datestr = '20.02.2013'
		myurl = 'http://zakupki.gov.ru/223/purchase/public/notification/search.html?purchase=&startingContractPriceFrom=&okvedCode=&okvedText=&customerOrgName=&searchWord=&startingContractPriceTo=&purchaseStages=APPLICATION_FILING&purchaseStages=COMMISSION_ACTIVITIES&purchaseStages=PLACEMENT_COMPLETE&customerOrgId=&customerOrgId=&okdpId=&purchaseMethodName=%3C%D0%92%D1%81%D0%B5+%D1%81%D0%BF%D0%BE%D1%81%D0%BE%D0%B1%D1%8B%3E&activeTab=0&okvedId=&okdpText=&okdpCode=&_purchaseStages=on&_purchaseStages=on&_purchaseStages=on&_purchaseStages=on&publishDateTo=&organName=&organName=&organName=&purchaseMethodId=&contractName=&fullTextSearchType=INFOS_AND_DOCUMENTS'
		datestr = '20.02.2013'
		page = self.request.get('page')
		logging.info('af with page %s' % page)
		params = '&d-3771889-p=%d&publishDateFrom=%s' % (int(page), datestr)
		logging.info('params %s' % params)
		lines = get_lines(myurl + params)
		
		
		links = get_links(lines)
		links.sort()
		
		logging.info('af with #links %s' % len(links))
		for link in links:
			keyname = link
			s = OrderLink.get_or_insert(keyname, url=link)
		#db.run_in_transaction(txn)


import xml.dom.minidom
from xml.dom.minidom import Node


# def get_snippets(body):
# 	body = body.encode('utf-8')
# 	dom = xml.dom.minidom.parseString(body)
# 	ps = dom.getElementsByTagName('p')
# 	snippets = []
# 	for p in ps:
# 		a = p.getElementsByTagName('a')
# 		i = p.getElementsByTagName('i')
# 		sn = (a.nodeValue, i.nodeValue)
# 		snippets.append(sn)
# 	return snippets

# <p>
#     	<a href="http://zakupki.gov.ru/223/purchase/public/purchase/info/common-info.html?purchaseId=100643&&purchaseMethodType=is"  target="_blank">http://zakupki.gov.ru/223/purchase/public/purchase/info/common-info.html?purchaseId=100643&&purchaseMethodType=is</a>
#     	<br>
#     	<i>Организация услуг питания на территории гостиницы “Radisson Blu Resort &amp; Congress Centre, Sochi”</i>
#     	</p>

def get_snippet(p):
	chunks = p.split('<i>')
	logging.info(chunks)
	desc = chunks[1].split('</i>')[0]
	link = chunks[0].split('"')[1]
	return (link, desc)

def get_snippets(body):
	ps = body.split('<p>')
	res =[]
	for p in ps:
		if '</p>' in p:
			res.append(get_snippet(p))
	return res

class Fetcher(webapp2.RequestHandler):
	def post(self):
		page = self.request.get('page')
		keyname = page
		logging.info('fetcher with page %s' % page)
		order_str = get_order(page).decode('utf-8')
		
		logging.info('fetcher with order %s' % order_str)
		
		s = OrderSnippet.get_or_insert(keyname, url=page, snippet=order_str)
		#db.run_in_transaction(txn)	

myurl = 'http://zakupki.gov.ru/223/purchase/public/purchase/info/common-info.html?purchaseId=84433&&purchaseMethodType=is'

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
	
def bad_entries_mc_key(date):
	return "bad_entries_%02d%02d%04d" % (date.day, date.month, date.year)

class BadRSSPrinter(FrontEnd):
	def get_bad_entries(self, date):
		key = bad_entries_mc_key(date)
		logging.info('key %s' % key)
		entries = memcache.get('%s' % key)
		if entries is not None:
			logging.info('found key %s' % key)
			return entries
		else:
			entries = self.render_entries(date)
			logging.info('missed key %s' % key)
			if not memcache.add(key, entries, time=exptime):
				logging.error('Memcache set failed.')
			return entries
			
	def render_entries(self, date):
		# query = RSSBadEntry.all()
# 		query.filter("date =", date)
		end = date + datetime.timedelta(days=1)
		logging.info('date start: %s' % date)
		logging.info('date end: %s' % end)
		query = db.GqlQuery('SELECT * FROM RSSBadEntry WHERE date >= :1 AND date <= :2',
                date, end)
		#query.order('url')
		entries = list(query)
		
		num_links = len(entries)
		msg = ''
		if num_links == 0:
			msg = ""
		template_values = {
			'num_links' : num_links,
			'entries'	: entries,
			'msg'       : msg,
		} 
		
		template = jinja_environment.get_template('boot2_bad.html')
		return template.render(template_values) 
			
	def get(self):
		date = self.request.get('date')
		logging.info('DATE %s' %date)
		try:
			date = datetime.datetime.strptime(date, '%d.%m.%Y')
		except:
			logging.warning('bad date in request, assuming current')
			date = day_date(datetime.datetime.now())
				
		entries = self.get_bad_entries(date)
		self.render_page(entries)


# class Guestbook(webapp2.RequestHandler):
#   def post(self):
#     # We set the same parent key on the 'Greeting' to ensure each greeting is in
#     # the same entity group. Queries across the single entity group will be
#     # consistent. However, the write rate to a single entity group should
#     # be limited to ~1/second.
#     guestbook_name = self.request.get('guestbook_name')
#     greeting = Greeting(parent=guestbook_key(guestbook_name))
# 
#     if users.get_current_user():
#       greeting.author = users.get_current_user().nickname()
# 
#     greeting.content = self.request.get('content')
#     greeting.put()
#     self.redirect('/?' + urllib.urlencode({'guestbook_name': guestbook_name}))

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
				keyname = entry.url
# 				daydate = datetime.datetime(year=entry.date.year, month=entry.date.month, 
# 								   day=entry.date.day)
				bad = RSSBadEntry.get_or_insert(keyname, url=entry.url, desc=entry.desc, bad=b, date=entry.date)
		mc_key = bad_entries_mc_key(date)
		memcache.delete(mc_key)
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
		


app = webapp2.WSGIApplication([('/', MainPage),
							   ('/admin_rss_entry', RSSEntryPrinter),
							   ('/admin_', AdminPage),
							   ('/bad', BadRSSPrinter),
							   ('/admin_clear_rss_index', ClearRSSIndex),
                               #('/sign', Guestbook),
                               ('/admin_doindex', IndexHandler),
                               ('/admin_fetch_addresses', AddressFetcher),
                               ('/admin_fetch_snippet', Fetcher),
                               ('/admin_index_rss_entries', IndexRSSEntries),
                               ('/admin_add_index_date', AddIndexeddate),
                               ('/admin_fetch', FetchHandler),
                               ('/admin_test_cron', TestCron),
                               ('/admin_fetch_rss', FetchRSS),
                               ('/admin_fetch_rss_batch',FetchRSSBatch)],
                              debug=True)
