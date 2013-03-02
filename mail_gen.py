# -*- coding: utf-8 -*-
import jinja2
import os


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

 
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

def hour_translator (hour):
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

def minute_translator(minute):
    if minute == 1 or minute == 21 or minute == 31 or minute == 41 or minute == 51:
        s = u'минута'
    elif 2 <= minute <= 4  or  22 <= minute <= 24 or  32 <= minute <= 34 or  42 <= minute <= 44 or  52 <= minute <= 54:
        s = u'минуты'
    else:
        s = u'минут'
    return s

def rus_words_form(words): 
    if len( words ) > 1:
        return u'русскоязычных словах'
    else:
        return u'русскоязычном слове'

def rus_letters_form(rus_letters): 
    if len(rus_letters) > 1:
        return  u'русских букв'
    else:
        return u'русской буквы'
    
        
def lat_letters_form_1(lat_letters): 
    if len(lat_letters) > 1:        
        return u'латинские буквы'
    else :     
        return u'латинскую букву'
       
         
def lat_letters_form_2(lat_letters): 
    if len(lat_letters) > 1:         
        return u'латинским буквам'
    else :    
        return u'латинской букве'
        
 
class MailGenerator( ):
    def gen_mail(self,params):
        template = jinja_environment.get_template('mail.html')
        return  template.render(params)   
        
        
        
        
        
        
        
        
        
        
#if __name__ == '__main__':
#        params = {
#         "id" : self.request.get('id'),
#         "desc": self.request.get('desc'),
#         "start_day": self.request.get('start_day'),
#         "start_month":  month_translator.get(self.request.get('start_month')),
#         "start_year": self.request.get('start_year'),
#         "finish_day": self.request.get('finish_day'),
#         "finish_month": month_translator.get(self.request.get('finish_month')),
#         "finish_year": self.request.get('finish_year'),
#         "hour": self.request.get('hour'),
#         "hour_form":hour_translator(self.request.get('hour')),
#         "minute_form":minute_translator(self.request.get('minute')),
#         "rus_words_form":rus_words_form(self.request.get('words')),
#         "rus_letters_form": rus_letters_form(self.request.get('russian_letters')),
#         "lat_letters_form_1": lat_letters_form_1(self.request.get('latin_letters')),
#         "lat_letters_form_2": lat_letters_form_2(self.request.get('latin_letters')),
#         "minutes": self.request.get('minutes'),
#         "price": self.request.get('price'),
#         "url": self.request.get('url'),
#         "words": self.request.get('words'),
#         "russian_letters": self.request.get('russian_letters'),
#         "latin_letters" : self.request.get('latin_letters'),
#         "buyer" : self.request.get('buyer'),
#         "address" : self.request.get('address'),
#         "telephone" : self.request.get('telephone'),
#         "fax" : self.request.get('fax'),
#         "mail" : self.request.get('mail'),
#         "name" : self.request.get('name'),
#         "curr_day" : d.day,
#         "curr_month": month_translator.get(d.month),
#         "curr_year" : d.year
#          }
#        d = datetime.now()
#        params = {
#         "id" : 1512,
#         "desc": u'куплю всякую бесполезную хуйню, дорого',
#         "start_day": 12,
#         "start_month":  month_translator.get(3),
#         "start_year": 2012,
#         "finish_day": 11,
#         "finish_month": month_translator.get(5),
#         "finish_year": 2013,
#         "hour": 12,
#         "hour_form":hour_translator(12),
#         "minutes_form":minute_translator(22),
#         "rus_words_form":rus_words_form([u'Лошарычи']),
#         "rus_letters_form": rus_letters_form(['f','e','g', 'v']),
#         "lat_letters_form_1": lat_letters_form_1(['f','e','g', 'v']),
#         "lat_letters_form_2": lat_letters_form_2(['f','e','g', 'v']),
#         "minutes": 22,
#         "price": 88,
#         "url": "kirill.html",
#         "words": " , ".join([u'Лошарычи']),
#         "russian_letters": " , ".join([u'я',u'ф',u'в',u'ш']),
#         "latin_letters" : " , ".join(['f','e','g', 'v']),
#          "buyer" :  u" ТЭЦ ЩМЭЦ",
#         "address" : u" вторая улица строителей г. Ленинград  дом 25 квартира 12",
#         "telephone" : "78654653213",
#         "fax" : "78654653213",
#         "mail" : 'mail@mail.com',
#         "name" : u'Казюбало Сергей Сергеевич',
#         "curr_day" : d.day,
#         "curr_month": month_translator.get(d.month),
#         "curr_year" : 2013
#         } 
