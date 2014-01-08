# -*- coding: utf-8 -*-
import json
import re

# return the emissions corresponding to the word token
def get_emissions(word, emit):
    def iscityname(wrd):
        cities = load_cities()
        return wrd in cities

    def isstatename(wrd):
        mailterms = ['Germany', 'Deutschland', 'Baden-Württemberg', 'Bayern', 'Berlin', 'Brandenburg', 'Bremen', 'Hamburg', 'Hessen', 'Mecklenburg-Vorpommern', 'Niedersachsen', 'Nordrhein-Westfalen', 'Rheinland-Pfalz', 'Saarland', 'Sachsen', 'Sachsen-Anhalt', 'Schleswig-Holstein', 'Thüringen']
        return wrd in mailterms
            
    def isroadname(wrd):
        wrd = wrd.lower()
        roadterms = ['str.', 'str', 'strasse', 'straße', 'platz', 'weg', 'allee', 'dorf', 'hof', 'garten', 'ring', 'wald', 'stadt', 'berg', 'bach', 'markt', 'höfe', 'hausen']
        for rt in roadterms:
            if wrd.endswith(rt):
                return True
        return False

    def ismailterm(wrd):
        wrd = wrd.lower()
        mailterms = ['address', 'adresse', 'anschrift', 'kontakt']
        for mt in mailterms:
            if mt in wrd:
                return True
        return False

    def isphonelike(wrd):
        if wrd.isdigit():
            return False
        phone = True 
        for c in wrd:
            if c not in '0123456789-() ':
                phone = False
                break
        return phone

    word = word.encode('utf8')
    has_comma, has_colon = False, False
    if word.endswith(','):
        word = word[:-1]
        has_comma = True
    if word.endswith(':'):
        word = word[:-1]
        has_colon = True

    ems = list()
    if re.match('^\d{5}(?:[-\s]\d{4})?$', word):
        ems.append(emit['ziplike'])
    elif re.match('/^([\+][0-9]{1,3}[\-])?([\(]{1}[0-9]{1,6}[\)])?([0-9\-]{5,12})?$/', word):
        ems.append(emit['phonelike'])
    elif word.isdigit() or re.match('^\d+(?:[-\/]{1}\d*)?(?:\w)?$', word): # can be 1A or 221-b 
        ems.append(emit['purenumber'])
    elif not word.isalpha() and word.isalnum():
        ems.append(emit['containsnumber'])
    elif ismailterm(word):
        ems.append(emit['mailterm'])
    elif isstatename(word):
        ems.append(emit['statename'])
    elif iscityname(word):
        ems.append(emit['cityname'])
    elif isroadname(word):
        ems.append(emit['roadname'])
    elif word.istitle():
        ems.append(emit['startcap'])
    else:
        ems.append(emit['default'])

    if has_comma:
        ems.append(emit['comma'])
    if has_colon:
        ems.append(emit['colon'])

    return ems

def replace_letters(word):
    word2 = word
    word2 = word2.replace('ü', 'ue')
    word2 = word2.replace('ö', 'oe')
    word2 = word2.replace('ä', 'ae')
    word2 = word2.replace('ß', 'ss')
    return word2

def load_cities(file='data/cities.csv'):
    cities = set()
    with open(file) as f:
        for line in f:
            city = line.strip()
            city2 = replace_letters(city)
            cities.add(city)
            cities.add(city2)
            # first part of multiword city
            cities.add(city.split()[0])
            cities.add(city2.split()[0])
    return cities

def read_labled_text(file, is_train):
    with open(file) as f:
        for read in f:
            jsontext = json.loads(read)
            text = jsontext['text'].replace('\n', ' ')
            if is_train:
                address = jsontext['address']
                frm = int(jsontext['address_from'])
                to = int(jsontext['to'])
                yield text, address, frm, to
            else:
                yield text

def text_emissions(file, emitcode, is_train=True):
    for inpt in read_labled_text(file, is_train):
        text = inpt
        if is_train:
            text, realadr, frm, to = inpt

        if is_train and realadr.startswith(','):
            print 'skipping', realadr
            continue

        emissions, original = list(), list()
        count, address, address_pos = 0, list(), 0
        for word in text.split():
            if is_train and count + len(word) + 1 > frm and count <= to:
                address.append(word)
            count += len(word) + 1

            em = get_emissions(word, emitcode)
            emissions.extend(em)

            original.append(word)
            if len(em) > 1:
                original.extend([''] * (len(em)-1))

            # increment until address found
            if len(address) == 0:
                address_pos += len(em)

            #print word, em
        if is_train:
            yield emissions, original, address_pos, address
        else:
            yield emissions, original
        

