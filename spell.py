# -*- coding: utf-8 -*-
import re, collections
import cydict
import filters

#words = cydict.__words

def read_words(fname, fltr):
  f = open(fname)
  res = []
  for line in f:
    line = line.decode('utf-8')
    chunks = line.split()
    for c in chunks:
      if fltr(c):
        res.append(c)
  return res

def train(features):
    model = collections.Counter(features)
    for f in features:
        model[f] += 1
    return model

#NWORDS = train(read_words('dict_law_ru.txt', filters.is_cyrillic))
#NWORDS = train(read_words('wp1.txt', filters.is_cyrillic))
#_lat = False
NWORDS = train(read_words('dict_eng_lit.txt', filters.is_latin))
_lat = True

_sample_lat = u'YourletteradshasgivenmgreatpleasureascaItshowsmethatcast'

_sample_lat2 = u'The Claimant alleged that one blog hosted by blogger.com contained material defaming him. He notified Google and, following a letter of claim a few weeks later, the blogger voluntarily removed the material. The Claimant subsequently brought an action for libel against Google for the period between notification and removal'
_sample_lat2 = "".join(_sample_lat2.split())

alphabet = u'йцукенгшщзхъёфывапролджэячсмитьбю'

if _lat:
  too_short = 3
else:
  too_short = 5

test_str_space = u'о т к р ы т ы й к о н к у р с н а п р а в о з а к л ю ч е н и я'
test_str = ''.join(test_str_space.split())

str2 = u'о т к р ы т ы й к о н к у р с н а п р а в о з а к л ю ч е н и я д о г о в о р а н а п р о в е д е н и е о б я з а т е л ь н о г о е ж е г о д н о г о а у д и т а б у х г а л т е р с к о й'


#test_str = u'ГражданскимкодексомРоссийскойФедерации'
# u'законами и иными нормативными правовыми актами Российской Федерации, а также принятыми в' \
# u'соответствии с ними и утвержденными с учетом положений  части 3 настоящей статьи правовыми актами'

#test_str = ''.join(test_str.split(u' ,.'))

def truncate_illegal(split):
  res = []
  for w in split:
    if NWORDS[w] == 0:
      break
    res.append(w)
  return tuple(res)

def all_illegal(wlist):
  for w in wlist:
    if NWORDS[w] > 0:
      return False
  return True

#avregae score 22
def score_words(wlist, truncate=False):
  res = 0
  for i,w in enumerate(wlist):
    score = NWORDS[w]
    if score == 0:
      #allow tail of the split to be illegal
      if truncate and all_illegal(wlist[i+1:]):
        return res
      else:
        return 0
    else:
      #downgrade little ones because they are so popular
      if len(w) < too_short:
        score = 1
      res += score*len(w)
  return res

def smaller_splits(word, allow_shorts):
  splits = [(word[:i], word[i:]) for i in range(1, len(word))]
  #optimization: don't return short splits
  res =[]
  for a,b in splits:
    if not allow_shorts and (len(a) < too_short or len(b) < too_short):
      continue
    res.append((a,b))
  return res


def all_split_lists(word, allow_shorts):
  """
  allow_shorts=False tells us to discard all splits with short words
  it is usually used when we already have one short word in split
  """
  #res is list of lists. each split is a list and we return list of splits
  res =  [ [word] ]
  for a,b in smaller_splits(word, allow_shorts):
    allow_further = allow_shorts
    if len(a) < too_short or len(b) < too_short:
      allow_further = False
    if NWORDS[a] > 0:
      for split in all_split_lists(b, allow_further):
        # if too_many_shorts(split):
        #   continue
        nsplit = [a]
        nsplit.extend(split)
        res.append( nsplit )
    if NWORDS[b] > 0:
      for split in all_split_lists(a, allow_further):
        # if too_many_shorts(split):
        #   continue
        split.append(b)
        res.append(split)
  return res

def unique_splits(split_list):
  """
  return a list of unique tuples (splits)
  """
  tup_set = set()
  for split in split_list:
    tup_set.add(tuple(split))
  return [t for t in tup_set]

def get_legal_splits_scores(word, truncate=False):
  scores = {}
  splits = unique_splits(all_split_lists(word, True))
  for split in splits:
    if truncate:
      split = truncate_illegal(split)
    score = score_words(split)
    if score > 0:
      scores[split] = score
  return scores


_chunk_size = 30

def truncated_splits(word):
  word = word.lower()
  trunc_val = min(_chunk_size, len(word))
  chunk = word[:trunc_val]

  for i in  reversed(range(1, len(chunk)+1)):
    scores = get_legal_splits_scores(chunk[:i], truncate=True)
    #return the longest interpreted legal split
    if len(scores) > 0:
      return scores
  return {}


def get_next_split(i, word):
  chunk = word[i:]
  score_dict = truncated_splits(chunk)
  if len(score_dict) == 0:
    return None
  splits = score_dict.keys()
  best_split = max(splits, key=score_dict.get)
  
  return (best_split, score_dict[best_split])


def interpret_text(text):
  text = text.lower()
  i = 0
  res = []
  while i < len(text):
    tup = get_next_split(i, text)
    if not tup:
      i += 1
      continue
    best_split = tup[0]
    length = match_len = sum([len(w) for w in best_split])
    i += length
    res.extend(list(best_split))
  return res



def scored_splits(word):
  """
  returns a list of tuples (splits) sorted by score, scores dict
  """
  word = word.lower()
  scores = get_legal_splits_scores(word)
  return scores








def edits1(word):
   splits     = [(word[:i], word[i:]) for i in range(len(word) + 1)]
   deletes    = [a + b[1:] for a, b in splits if b]
   transposes = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b)>1]
   replaces   = [a + c + b[1:] for a, b in splits for c in alphabet if b]
   inserts    = [a + c + b     for a, b in splits for c in alphabet]
   #joins      = get_joins(word)
   return set(deletes + transposes + replaces + inserts )#+ joins)

def known_edits2(word):
    return set(e2 for e1 in edits1(word) for e2 in edits1(e1) if e2 in NWORDS)

def known(words): return set(w for w in words if w in NWORDS)

def correct(word):
    candidates = known([word]) or known(edits1(word)) or known_edits2(word) or [word]
    #return max(candidates, key=NWORDS.get)
    clist = list(candidates)
    clist.sort(key=NWORDS.get)
    return clist

def is_legal(word):
  return NWORDS[word] > 0

def test():
  print u'закупки', is_legal(u'закупки')
  print u'закупка', is_legal(u'закупка')
  print u'зкупка', is_legal(u'зкупка')
  for w in correct(u'зкупка'):
    print w

def test_join1():
  print score_words([u'за', u'ку', u'пки'])
  print score_words([u'за', u'купк', u'и'])
  print score_words([u'закупки'])
  print score_words([u'жопа'])


def test_join2():
  count = 0
  sum = 0
  for w,score in NWORDS.most_common():
    sum += score
    count += 1
  print 'avregae score', (sum/count)

def test_join3():
  print all_split_lists('abc')

def test_join4(word):
  score_dict = scored_splits(word)
  splits = score_dict.keys()
  splits.sort(key=score_words)
  for split in splits:
    print ",".join(split), score_dict[split]
  return splits

def test_join5(spaced_word):
  word = ''.join(spaced_word.split())
  test_join4(word)


def test_join6(word):
  score_dict = truncated_splits(word)
  splits = score_dict.keys()
  splits.sort(key=score_words)
  for split in splits:
    print ",".join(split), score_dict[split]
  return splits


def test_join7(word):
  tup = get_next_split(0,word)
  split = tup[0]
  length = match_len = sum([len(w) for w in split])
  score = tup[1]
  print ",".join(split), score, length


_sample_text = u'уклонившимсялвслотзаключенияконтракталиывлызаказчиквправеобратитьсясудтребованиемопонуждениипобедителяаукционазаключитькон'

def test_join8(text):
  words = interpret_text(text)
  print ",".join(words)


if __name__ == '__main__':
  test_join3()
  #print get_joins('t e s t')
  # for w in correct(u'з а к о н'):
  #   print w
  # words = get_joins(u'т е с т')
  # words = set(words)
  # for w in words:
  #   print w
  # for w in correct(u'зкпка'):
  #   print w

