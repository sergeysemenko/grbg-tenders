import unicodedata

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

def scan(body):
	filter_list = [is_interleaved_body]
	for f in filter_list :
		bad = f(body)
		if bad:
			return bad

##############################################

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


