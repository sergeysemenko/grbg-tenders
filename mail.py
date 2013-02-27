# -*- coding: utf-8 -*-
from docx import import *

if __name__ == '__main__':
    # Default set of relationshipships - the minimum components of a document
    relationships = relationshiplist()

    # Make a new document tree - this is the main part of a Word document
    document = newdocument()

    # This xpath location is where most interesting content lives
    body = document.xpath('/w:document/w:body', namespaces=nsprefixes)[0]

    
    body.append(paragraph(u'                    В Федеральную антимонопольную службу России'
                          ))

    title    = 'Python docx demo'
    subject  = 'A practical example of making docx from Python'
    creator  = 'Mike MacCana'
    keywords = ['python', 'Office Open XML', 'Word']

    coreprops = coreproperties(title=title, subject=subject, creator=creator,
                               keywords=keywords)
    appprops = appproperties()
    contenttypes = contenttypes()
    websettings = websettings()
    wordrelationships = wordrelationships(relationships)

    # Save our document
    savedocx(document, coreprops, appprops, contenttypes, websettings,
             wordrelationships, 'Welcome to the Python docx module.docx')