import json
import requests
from urllib.parse import urlencode
from urllib.request import urlopen
import mwparserfromhell
import pywikibot
import time as t
import config

edit_protected = []
api_base = "https://en.wikipedia.org/w/api.php?format=json&action=query&list=allpages&apprtype="
api_end = "&apfilterredir=nonredirects&apprlevel=autoconfirmed&aplimit=500&apcontinue="
username = 'TheMagikBOT'
password = config.password()
baseurl = 'https://en.wikipedia.org/w/'
summary = 'Added page protection template where none existed'



#Get a list of all edit protected pages
def get_edit_protected():
    last_continue = ""
    
    while True:
        global api_base
        global api_end
        
        full_url = api_base + "edit" + api_end + last_continue

        response = requests.get(full_url)
        data = response.json()

        pages = data['query']['allpages']

        if 'continue' in data:
            for item in pages:
                edit_protected.append(item.get('title'))
                last_continue = data['continue']['apcontinue']
        else:
            return 1


def parse(title):
    site = pywikibot.Site()
    page = pywikibot.Page(site, title)
    text = page.get()
    return mwparserfromhell.parse(text)


def allow_bots(text, user): #Verify that TheMagikBOT is allowed to edit the page
    user = user.lower().strip()
    text = mwparserfromhell.parse(text)
    for tl in text.filter_templates():
        if tl.name in ('bots', 'nobots'):
            break
    else:
        return True
    for param in tl.params:
        bots = [x.lower().strip() for x in param.value.split(",")]
        if param.name == 'allow':
            if ''.join(bots) == 'none': return False
            for bot in bots:
                if bot in (user, 'all'):
                    return True
        elif param.name == 'deny':
            if ''.join(bots) == 'none': return True
            for bot in bots:
                if bot in (user, 'all'):
                    return False
    return True


def add(title, message):
    # Login request
    payload = {'action': 'query', 'format': 'json', 'utf8': '', 'meta': 'tokens', 'type': 'login'}
    r1 = requests.post(baseurl + 'api.php', data=payload)

    # login confirm
    login_token = r1.json()['query']['tokens']['logintoken']
    payload = {'action': 'login', 'format': 'json', 'utf8': '', 'lgname': username, 'lgpassword': password, 'lgtoken': login_token}
    r2 = requests.post(baseurl + 'api.php', data=payload, cookies=r1.cookies)

    # get edit token2
    params3 = '?format=json&action=query&meta=tokens&continue='
    r3 = requests.get(baseurl + 'api.php' + params3, cookies=r2.cookies)
    edit_token = r3.json()['query']['tokens']['csrftoken']

    edit_cookie = r2.cookies.copy()
    edit_cookie.update(r3.cookies)

    # save action
    payload = {'action': 'edit', 'assert': 'user', 'format': 'json', 'utf8': '', 'bot' : 'True', 'minor' : 'True', 'prependtext': message,'summary': summary, 'title': title, 'token': edit_token}
    r4 = requests.post(baseurl + 'api.php', data=payload, cookies=edit_cookie)

    print (r4.text)

    n += 1
    t.sleep(0.5)
        
        

def find_protection_level(title):
    #Normalise URL with underscore for space
    title = title.replace(" ", "_")
    
    #Create full query URL
    api_base = "https://en.wikipedia.org/w/api.php?action=query&titles="
    api_end = "&prop=info%7Cflagged&inprop=protection&format=json"
    api_link = api_base + title + api_end
    
    #JSON response
    request = requests.get(api_link)
    data = request.json()

    try: #Pending changes
        #Find protection level
        number = list((data['query']['pages'])) #Unique page reference
        data = (data['query']['pages'][number[0]]['flagged']['protection_level'])
        print(data)
        return "pending_changes"
    
    except KeyError: #edit or move protected - follow same api structure
        try:
            number = list(data['query']['pages'])
            data = data['query']['pages'][number[0]]['protection'][0]['type']
            return data
        
        except:
            return None
        
def find_protection_level(title):
    #Normalise URL with underscore for space
    title = title.replace(" ", "_")
    
    #Create full query URL
    api_base = "https://en.wikipedia.org/w/api.php?action=query&titles="
    api_end = "&prop=info%7Cflagged&inprop=protection&format=json"
    api_link = api_base + title + api_end
    
    #JSON response
    request = requests.get(api_link)
    data = request.json()

    try: #Pending changes
        #Find protection level
        number = list((data['query']['pages'])) #Unique page reference
        data = (data['query']['pages'][number[0]]['flagged']['protection_level'])
        return "pending_changes"
    
    except KeyError: #edit or move protected - follow same api structure
        try:
            number = list(data['query']['pages'])
            data = data['query']['pages'][number[0]]['protection'][0]['type']
            return data
        
        except:
            return None
        


get_edit_protected()

for title in edit_protected:

    try: #protection sometimes not shown in API
        protection_level = find_protection_level(title)
    except:
        protection_level = None
        print(title, 'Error')    
    
        
    if protection_level == 'edit' or 'autoconfirmed': #semi protected
        try:
            data = parse(title)
            templates = data.filter_templates()

            if any("{{pp" in title.lower() for title in templates): #all templates that produce padlock icon
                continue

            elif any("{{semiprotected" in title.lower() for title in templates):
                continue

            elif any("{{rcat shell" in title.lower() for title in templates):
                continue

            elif any("{{sprotected" in title.lower() for title in templates):
                continue

            else:
                if allow_bots(data, 'TheMagikBOT') == True:
                    add(title, '{{pp|small=yes}} \n')
                    print(title)
                    continue
        except:
            t.sleep(20)
            continue
