# -*- coding: utf-8 -*-
import datetime
import urllib2
import logging
import HTMLParser
import core



rss_url = "http://zakupki.gov.ru/223/purchase/public/notice-search-rss.html?"
static_params = "okvedText=&searchWord=&organName=&organName=&organName=&okdpText=&purchase=&activeTab=0&okdpId=&d-3771889-p=5&purchaseStages=APPLICATION_FILING&purchaseStages=COMMISSION_ACTIVITIES&purchaseStages=PLACEMENT_COMPLETE&fullTextSearchType=INFOS_AND_DOCUMENTS&customerOrgName=&customerOrgId=&customerOrgId=&purchaseMethodName=%3C%D0%92%D1%81%D0%B5%20%D1%81%D0%BF%D0%BE%D1%81%D0%BE%D0%B1%D1%8B%3E&okvedCode=&purchaseMethodId=&startingContractPriceFrom=&publishDateTo=&okdpCode=&publishDateFrom=21.02.2013&contractName=&startingContractPriceTo=&_purchaseStages=on&_purchaseStages=on&_purchaseStages=on&_purchaseStages=on&okvedId="

price_params_tmpl = '&startingContractPriceTo=%s&startingContractPriceFrom=%s&'
date_params_tmpl = '&publishDateFrom=%s&publishDateTo=%s&'

# there is for sure less than 200 entries after price_tail  
price_tail = 6100000

rss_desc_tag = u'Наименование закупки:'
rss_author_tag = u'Заказчик:'

def decode_rss_content(content, tag):
    """
    @param content: content:encoded part of the rss item, unicode()
    @param tag: the tag in the content:encoded part like Наименование закупки:,
                unicode() object
    """
    value = None
    try:
        h = HTMLParser.HTMLParser()
        content = content.encode('utf-8')
        value = content.split(tag.encode('utf-8'))[1]
        value = h.unescape(value.decode('utf-8')).encode('utf-8')
        value = value.split('>')[1]
        value = value.split('<')[0]
    except:
        logging.error('PARSE_RSS_CONTENT_ERROR: content: %s \ntag: %s' % (content, 
                       tag.encode('utf-8')))
    return value

class ParsedRSSEntry:
    def __init__(self, edict):
        """
        @param edict: {'link' : unicode(), 
                       'content:encoded' : unicode(), 
                       'pubDate' : unicode()}
                       generated by parse_rss_chunk()
                      
        self.link:      raw_str
        self.desc:      raw_str, value of  u'Наименование закупки:'
        self.published: raw_str, date published
        self.published_parsed: datetime.datetime.now()
        self.content:   unicode(), value of <content:encoded>
        """
        self.link = edict['link'].encode('utf-8')
        self.content = edict['content:encoded']
        self.desc = decode_rss_content(self.content, rss_desc_tag)
        self.author = decode_rss_content(self.content, rss_author_tag)
        self.published = edict['pubDate'].encode('utf-8')
        self.published_parsed = datetime.datetime.strptime(self.published, 
                                                  '%a, %d %b %Y %H:%M:%S %Z')
    
    def valid(self):
        return self.desc != None and self.author != None    
    
    def __str__(self):
        return 'link: %s\n desc:%s\n published:%s\n published_parsed:%s' % (self.link, 
            self.desc, self.published, self.published_parsed)
    

def parse_tag_chunk(tag, text):
    """
    @param tag: raw_str, xml tag like link or pubDate
    @param text: unicode(), text to search tag 
    
    @return tag_value: unicode(), content of tag (xmlNode.text)
    """
    chunks = text.split('<%s>' % tag)
    val = chunks[1].split('</%s>' % tag)[0]
    return val
    
"""
Malformed chunk example:
PARSE_RSS_CHUNK_ERROR: tagcontent:encoded 
chunk:&lt;br/&gt;&lt;b&gt;Заказчик:&amp;nbsp;&lt;/b&gt;Общество с ограниченной ответственностью "Агенда"&lt;br/&gt;&lt;b&gt;Способ размещения закупки:&amp;nbsp;&lt;/b&gt;Открытый конкурс в электронной форме&lt;br/&gt;&lt;b&gt;Дата публикации извещения:&amp;nbsp;&lt;/b&gt;05.02.2013&lt;br/&gt;</content:encoded>
      <pubDate>Tue, 05 Feb 2013 12:27:39 GMT</pubDate>
      <guid isPermaLink="false">910edfeb-b7e2-41dc-89ec-9a30ea72e5f6</guid>
    </
"""


def parse_rss_chunk(chunk):
    """
    @param chunk: raw_str, everything between <item> tags in rss stream
    
    @return edict: {'link' : unicode(), 
                    'content:encoded' : unicode(), 
                    'pubDate' : unicode()}
    """
    edict = {'link' : None, 'content:encoded' : None, 'pubDate' : None}
    for tag in edict.keys():
        if tag not in chunk:
            logging.error('PARSE_RSS_CHUNK_ERROR: no tag%s in chunk:%s' % (tag, chunk))
            return None
        else:
            try:
                val = parse_tag_chunk(tag, chunk)
            except:
                logging.error('PARSE_RSS_CHUNK_ERROR: tag%s \nchunk:%s' % (tag, chunk))
                return None
            edict[tag] = val
    return edict

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
    content = core.get_content(myurl)
    chunks = content.decode('utf-8').split('item')
    entries = []
    for chunk in chunks:
        if 'pubDate' in chunk:
            edict = parse_rss_chunk(chunk)
            if edict:   
                entry = ParsedRSSEntry(edict)
                if entry.valid():
                    entries.append(entry)
    return entries

def keyname_from_link(link):
    pcs = link.split('purchaseId=')
    id = pcs[1].split('&')[0]
    return str(int(id))    
    
if __name__ == '__main__':
    print len(fetch_rss_by_range2('1.2.2013', '100000', '0'))