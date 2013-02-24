# -*- coding: utf-8 -*-
from datetime import datetime
from google.appengine.api import search
import models
import logging
import sortoptions
import filters

debug_index_name = 'rss_entries_index'

def create_document(entry, docid, fixed=False):
    # IMPORTANT TO LOWERCASE FIELDS. SEARCH APPARENTLY LOWERCASES INPUT
    # QUERIS - SO WORDS     CAPITAL LETTERS WILL NOT BE FOUND!!!!!!!!!
    fields=[search.TextField(name='url', value=entry.url),
                search.TextField(name='author', value=entry.author.lower()),
        search.TextField(name='desc', value=entry.desc.lower()),
                search.HtmlField(name='content', value=entry.content.lower()),
                search.DateField(name='date', value=entry.date)]
    if fixed : #and hasattr(entry, 'desc_fixed'):
        fields.append(
            search.TextField(name='desc_fixed', value=entry.desc_fixed.lower())
            )
    return search.Document(fields=fields)

def index_entry(entry, docid, index_name=debug_index_name, fixed=False):
    # Get the index.
    index = search.Index(name=index_name)

    # TODO(grbg): transaction, mutex?
    doc = index.get(docid)
    if doc:
        #TODO(grbg): if it's slow, check if update+put doesn't duplicate doc
        index.delete([docid])
    
    doc = create_document(entry, docid, fixed=fixed)

    # Index the document.
    try:
        index.put(doc)
    # except search.PutError, e:
    #     result = e.results[0]
    #     if result.code == search.OperationResult.TRANSIENT_ERROR:
    #         # possibly retry indexing result.object_id
    except search.Error, e:
        logging.error('index error: %s' % str(e))

def clear_index(index_name=debug_index_name, limit=100):
    # Get the index.
    index = search.Index(name=index_name)
    logging.info('clearing index %s' % index_name)
    response = index.get_range(limit=limit, ids_only=True)
    is_clear = len(response.results) > 0
    try:
        ids = [doc.doc_id for doc in response.results]
        index.delete(ids)
        logging.info('deleted %d docs from index %s' % (len(ids), index_name))
    except search.Error, e:
        logging.error('delete index error: %s' % str(e))
    return is_clear


class MSearchResult(object):

    def __init__(self, doc):
        self.doc = doc

    def get_field_val(self, fname):
        """Get the value of the document field with the given name.  If there is
        more than one such field, the method returns None."""
        try:
          return self.doc.field(fname).value
        except ValueError:
          return None

    def author(self):
        return self.get_field_val('author')

    def desc(self):
        return self.get_field_val('desc')

    def desc_fixed(self):
        return self.get_field_val('desc_fixed')

    def decorated(self):
        return filters.decorate_body(self.desc()).decode('utf-8')

    def fixed_decorated(self):
        return filters.decorate_body_all(self.desc_fixed()).decode('utf-8')

    def url(self):
        return self.get_field_val('url')

    def date(self):
        return self.get_field_val('date')

import HTMLParser

def search_entries(query='date > 2013-02-22 date < 2013-02-24',
                    index_name=debug_index_name, date=None,
                    hidden=False):
    # Query the index.
    # expr_list = [
    #   search.SortExpression(expression='author', default_value='',
    #                         direction=search.SortExpression.DESCENDING)]
    # soption = sortoptions.get_sort_options()
    logging.info('searching for query: %s' % query)
    index = search.Index(name=index_name)
    try:
        querystr = query#'(desc:%s OR author:%s)' %(query, query)
        if date:
            querystr += '  date > %s-%s-%s' % (
                date.year, date.month, date.day)
        returned_fields=['url', 'author', 'date', 'desc', 'desc_fixed']
        if hidden:
            returned_fields.append('desc_fixed')
        results = index.search(search.Query(
            # Specify the query string using the Search API's Query language.
            query_string=querystr,
            options=search.QueryOptions(
                limit=20,
                cursor=search.Cursor(),
                sort_options=search.SortOptions(
                    expressions=[ ],
            #search.SortExpression(expression='date', default_value='')],
                    limit=1000),
                returned_fields=returned_fields,
                snippeted_fields=[])))

        # search by date:
        # date > 2012-01-01
        # date >= 2013-02-11  date < 2013-02-12 gives date 11
        #results = index.search(query)
        logging.info('found %d results' % len(results.results))
        logging.info('type q: %s' % type(query))
        # Iterate through the search results.
        res_list = [MSearchResult(doc) for doc in results]
        # for scored_document in results:
        #     # process the scored_document
        #     get_field_val(doc, fname)
        return res_list
    except search.Error, e:
        # possibly log the failure
        logging.error("Search ERROR ")
        return []





