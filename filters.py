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

def filter(body):
	filters = [is_interleaved_body]
	for f in filters :
		bad =  f(body)
		if bad:
			return bad
			