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
api_end = "&apfilterredir=nonredirects&apprlevel=autoconfirmed&aplimit=500&rvslots=main&apcontinue="
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
    site = pywikibot.Site()
    page = pywikibot.Page(site, title)

    text = page.text

    text = message + text

    try:
        if page.text != text:
            print(title)
            page.text = text
            page.save(summary=summary, minor=True, botflag=True)
    except Exception as exception:
        print(exception)

        
def find_protection_level(title):
    #Normalise URL with underscore for space
    title = title.replace(" ", "_")
    
    #Create full query URL
    api_base = "https://en.wikipedia.org/w/api.php?action=query&titles="
    api_end = "&prop=info%7Cflagged&inprop=protection&format=json&rvslots=main"
    api_link = api_base + title + api_end
    
    #JSON response
    request = requests.get(api_link)
    data = request.json()

    try: #Pending changes follows this api result structure
        #Find protection level
        number = list((data['query']['pages'])) #Unique page reference
        data = (data['query']['pages'][number[0]]['flagged']['protection_level'])
        print(data)
        return "pending_changes"
    
    except KeyError: #edit or move protected, both follow same api structure
        try:
            number = list(data['query']['pages'])
            data = data['query']['pages'][number[0]]['protection'][0]['type']
            return data
        
        except: #Neither pending changes nor edit/move protected
            return None
        

get_edit_protected()
#edit_protected = edit_protected[::-1] #Can be used to reverse list of end has not been done in a while.

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

            if any("{{pp" in title.lower() for title in templates): #all these templates that produce padlock icon
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
        except:
            t.sleep(20)
            continue

print("Done!")
