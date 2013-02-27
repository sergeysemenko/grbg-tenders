# -*- coding: utf-8 -*-
from datetime import datetime
 
month_translator = {
                      1:u'января',
                      2:u'февраля',
                      3:u'марта',
                      4:u'апреля',
                      5:u'мая',
                      6:u'июня',
                      7:u'июля',
                      8:u'августа',
                      9:u'сентября',
                      10:u'октября',
                      11:u'ноября',
                      12:u'декабря' }

def hour_tranlsator (hour):
    if hour == 0:
        s = u'часов'
    if hour == 1  or hour == 21:
        s = u'час'
    if  1 < hour < 5:
        s = u'часа'
    if hour > 21:
        s = u'часа'
    if  4 < hour < 21:
        s = u'часов'
    return s

def minute_tranlator(minute):
    if minute == 1 or minute == 21 or minute == 31 or minute == 41 or minute == 51:
        s = u'минута'
    elif 2 <= minute <= 4  or  22 <= minute <= 24 or  32 <= minute <= 34 or  42 <= minute <= 44 or  52 <= minute <= 54:
        s = u'минуты'
    else:
        s = u'минут'
    return s
        
def format_appeal(params):
    fh = open('template.txt')
    dest = open('appeal.txt' , 'w')
    i = 1
    day = params.get("day")
    month = month_translator.get (params.get("month"))
    year = params.get("year")
    hour_form = hour_tranlsator(params.get("hour"))
    minutes_form = minute_tranlator (params.get("minutes"))
    sub_day = params.get("submission_day")
    sub_month = month_translator.get(params.get("submission_month"))
    sub_year = params.get("submission_year")
   
    if len(params.get("words")) > 1:
        form_1 = u'русскоязычных словах'
    else:
        form_1 = u'русскоязычном слове'
    
    if len(params.get("russian_letters")) > 1:
        form_2 = u'русских букв'
        form_3 = u'латинские буквы'
        form_4 = u'латинским буквам'
    else:
        form_2 = u'русской буквы'
        form_3 = u'латинскую букву'
        form_4 = u'латинской букве'
 
    d = datetime.now()
    
    for line in fh.readlines():
        if i == 19:
            line = line.format(sub_day, sub_month, sub_year, params.get("id"), params.get("desc"))
        if i == 20:
            line = line.format(params.get("price"))
        if i == 21:
            line = line.format(params.get("url"))
        if i == 22:
            line = line.format(day, month, year, params.get("hour"), hour_form, params.get("minutes"), minutes_form)
        if i == 26:
            line = line.format(form_1, " , ".join(params.get("words")), form_2, " , ".join(params.get("russian_letters")), form_3, " , ".join(params.get("latin_letters")))
        if i == 29:
            line = line.format(form_4, " , ".join(params.get("latin_letters")))
        if i == 44:
            line = line.format(d.day , month_translator.get(d.month), d.year)        
        i = i + 1
        dest.write(line)
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
if __name__ == '__main__':
    p = {
         "id" : 300,
         "desc": u'хочу купить много всякой разной хуйни',
         "submission_day":11,
         "submission_month":3,
         "submission_year":1045,
         "price":50000,
         "url":"http://www.diveintopython.net/native_data_types/mapping_lists.html",
         "day":11,
         "month": 1,
         "year":2034,
         "hour":22,
         "minutes":11,
         "words": [u'ываываыв', u'йываыва'],
         "russian_letters": [u'ф', u'й'],
         "latin_letters" :["f", "s"],
          }
    format_appeal(p)
