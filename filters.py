# -*- coding: utf-8 -*-
import unicodedata

def is_cyrillic(word):
    for c in word:
        if not is_cyrillic_char(c):
            return False
    return True

def is_latin(word):
    for c in word:
        if not is_latin_char(c):
            return False
    return True

def is_latin_cyrillic(word):
    for c in word:
        if not is_latin_char(c) and not is_cyrillic_char(c):
            return False
    return True

def is_interleaved(word):
    return (is_latin_cyrillic(word) and 
            not is_cyrillic(word)   and 
            not is_latin(word))

def is_interleaved_body(body):
    for word in body.split():
        if is_interleaved(word):
            return word
    return None

def is_cyrillic_char(c):
    return 'CYRILLIC' in unicodedata.name(c)

def is_latin_char(c):
    return 'LATIN' in unicodedata.name(c)

def scan(body):
    filter_list = [is_interleaved_body]
    for f in filter_list :
        bad = f(body)
        if bad:
            return bad

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

def decorate_body_all(body):
    res = []
    if body:
        for word in body.split():
            word = decorate(word)
            res.append(word.encode('utf-8'))
        return " ".join(res)
    else:
        return "NO FIXED DESC YET"

cy_2_lat = {
    u'а':  u'a',
    u'в' : u'b',
    u'е' : u'e',
    u'к' : u'k',
    u'м' : u'm',
    u'н' : u'h',
    u'о' : u'o',
    u'р' : u'p',
    u'с' : u'c',
    u'т' : u't',
    u'у' : u'y',
    u'х' : u'x',
    }

lat_2_cy = {v:k for k, v in cy_2_lat.items()}

def interleaved_to_lang(word, ldict):
    res = u''
    for c in word:
        res += ldict.get(c, c)
    return res

def fix_body(body):
    body = body.lower()
    res = []
    for word in body.split():
        res.append(word)
        if is_interleaved(word):
            ldicts = [cy_2_lat, lat_2_cy]
            fixed_words = [interleaved_to_lang(word, ldict) for ldict in ldicts]
            res.extend([fxword for fxword in fixed_words])
    return " ".join(res)


if __name__ == '__main__':
    body = u'interleaved: TесT cy: Тест lat: Tect '

    print decorate_body_all(fix_body(body))

        








