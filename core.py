# -*- coding: utf-8 -*-
import urllib2
import unicodedata

def get_content(url):
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0'), 
    					 ("Accept-Encoding", 'UTF-8')]
    response = opener.open(url)
    return response.read()


