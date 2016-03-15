# -*- coding: utf-8 -*-
# Requires PyCurl, Feedparser, BeautifulSoup, PyQt4
import feedparser
import re
import urllib
import urllib2
import httplib
import codecs
import base64
from module.network.RequestFactory import getURL 
from BeautifulSoup import BeautifulSoup
import pycurl
import time

try:
    import simplejson as json
except ImportError:
    import json

# Jdownloader
def write_crawljob_file(package_name, folder_name, link_text, crawljob_dir):
    crawljob_file = crawljob_dir + '/%s.crawljob' % package_name.replace(' ', '')

    file = open(crawljob_file, 'w')
    file.write('enabled=TRUE\n')
    file.write('autoStart=TRUE\n')
    file.write('extractAfterDownload=TRUE\n')
    file.write('downloadFolder=%s\n' % folder_name)
    file.write('packageName=%s\n' % package_name.replace(' ', ''))
    file.write('text=%s\n' % link_text)
    file.close()
    
# MovieBlog
def notifyPushbulletMB(apikey,text):
    if apikey == "0" or apikey == "":
        return
    postData = '{"type":"note", "title":"FeedRss: Link hinzugefügt", "body":"%s"}' %" ### ".join(text).encode("utf-8")
    c = pycurl.Curl()
    c.setopt(pycurl.WRITEFUNCTION, lambda x: None)
    c.setopt(pycurl.URL, 'https://api.pushbullet.com/v2/pushes')
    c.setopt(pycurl.HTTPHEADER, ['Content-Type: application/json'])
    c.setopt(pycurl.USERPWD, apikey.encode('utf-8'))
    c.setopt(pycurl.POST, 1)
    c.setopt(pycurl.POSTFIELDS, postData)
    c.perform()

class MovieblogFeed():
    __config__ = [("interval", "int", "Execution interval in minutes", "15"),
                  ("patternfile", "str", "File to search for tv-shows, movies...", "/config/Filme.txt"),
                  ("destination", "queue;collector", "Link destination", "collector"),
                  ("ignore","str","Ignore pattern (comma seperated)","ts,cam,subbed,xvid,dvdr,untouched,pal,md,ac3md,mic"),
                  ("historical","bool","Use the movie-blog.org search in order to match older entries","False"),
                  ("pushbulletapi","str","Your Pushbullet-API key","o.kfJEpgOLWs4a9htnBzI29d9vEaRieFZj"),
                  ("quiethours","str","Quite hours (comma seperated)","")]
   
    FEED_URL = "http://www.movie-blog.org/feed/"
    SUBSTITUTE = "[&#\s/]"
    
    def activate(self):
        self.periodical.start(self.config.get('interval') * 60)
        
    def readInput(self):
        try:
            f = codecs.open(self.config.get("patternfile"), "rb")
            return f.read().splitlines()
        except:
            self.log_error("Inputfile not found")
            
    def getPatterns(self):
        out = {}
        for line in self.mypatterns:
            if len(line) == 0 or line.startswith("#"):
                continue
            try:
                n = line.split(",")[0]
                q = line.split(",")[1]
                r = line.split(",")[2]
            except:
                self.log_error("Syntax error in [%s] detected, please take corrective action" %self.config.get("patternfile"))
            
            try:
                d = line.split(",")[3]
            except:
                d = ""
            
            if q == "":
                q = r'.*'
                
            if r == "":
                r = r'.*'

            out[n] = [q,r,d]
        return out
        
    def searchLinks(self):
        ignore = self.config.get("ignore").lower().replace(",","|") if not self.config.get("ignore") == "" else "^unmatchable$"
        for key in self.allInfos:
            s = re.sub(self.SUBSTITUTE,".",key).lower()
            for post in self.feed.entries:
                """Search for title"""
                found = re.search(s,post.title.lower())
                if found:
                    """Check if we have to ignore it"""
                    found = re.search(ignore,post.title.lower())
                    if found:
                        self.log_debug("Ignoring [%s]" %post.title)
                        continue
                    """Search for quality"""
                    ss = self.allInfos[key][0].lower()
                    if ss == "480p":
                        if "720p" in post.title.lower() or "1080p" in post.title.lower() or "1080i" in post.title.lower():
                            continue
                        found = True
                    else:
                        found = re.search(ss,post.title.lower())
                    if found:
                        """Search for releasegroup"""
                        sss = "[\.-]+"+self.allInfos[key][1].lower()
                        found = re.search(sss,post.title.lower())
                        if found:
                            destination = self.allInfos[key][2].lower()
                            try:
                                episode = re.search(r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*',post.title.lower()).group(1)
                                if "repack" in post.title.lower():
                                    episode = episode + "-repack"
                                self.log_debug("TV-Series detected, will shorten its name to [%s]" %episode)
                                self.dictWithNamesAndLinks[episode] = [post.link, destination]
                            except:
                                self.dictWithNamesAndLinks[post.title] = [post.link, destination]        
    
    
    def quietHours(self):
        hours = self.config.get("quiethours").split(",")        
        if str(time.localtime()[3]) in hours:
            self.log_debug("Quiet hour, nothing to do!")
            return True
        else:
            return False
    
    def periodical_task(self):
        if self.quietHours():
            return
            
        urls = []
        text = []
        self.mypatterns = self.readInput()
        
        self.dictWithNamesAndLinks = {}
        self.allInfos = self.getPatterns()
        
        if self.config.get("historical"):
            for xline in self.mypatterns:
                if len(xline) == 0 or xline.startswith("#"):
                    continue
                xn = xline.split(",")[0].replace(".", " ").replace(" ", "+")
                urls.append('http://www.movie-blog.org/search/%s/feed/rss2/' %xn)
        else:
            urls.append(self.FEED_URL)

        for url in urls:
            self.feed = feedparser.parse(url)
            self.searchLinks()

        for key in self.dictWithNamesAndLinks:
            if not self.db.retrieve(key) == 'added':
                self.db.store(key, 'added')
                write_crawljob_file(key, key, [self.dictWithNamesAndLinks[key][0]],
                    config.crawljob_directory)
                text.append(key)
            else:
                self.log_debug("[%s] has already been added" %key)
        if len(text) > 0:
            notifyPushbulletMB(self.config.get("pushbulletapi"),text)

# Serienjunkies
def getSeriesList(file):
    try:
        titles = []
        f = codecs.open(file, "rb", "utf-8")
        for title in f.read().splitlines():
            if len(title) == 0:
                continue
            title = title.replace(" ", ".")
            titles.append(title)
        f.close()
        return titles
    except UnicodeError:
        self.core.log.error("Abbruch, es befinden sich ungueltige Zeichen in der Suchdatei!")
    except IOError:
        self.core.log.error("Abbruch, Suchdatei wurde nicht gefunden!")
    except Exception, e:
        self.core.log.error("Unbekannter Fehler: %s" %e)
   
def notifyPushbulletSJ(api='', msg=''):
    data = urllib.urlencode({
        'type': 'note',
        'title': 'FeedRss: Link hinzugefügt',
        'body': "\n\n".join(msg)
    })
    auth = base64.encodestring('%s:' %api).replace('\n', '')
    try:
        req = urllib2.Request('https://api.pushbullet.com/v2/pushes', data)
        req.add_header('Authorization', 'Basic %s' % auth)
        response = urllib2.urlopen(req)
    except urllib2.HTTPError:
        print 'Failed much'
        return False
    res = json.load(response)
    if res['sender_name']:
        print 'Pushbullet Success'
    else:
        print 'Pushbullet Fail'

class SJ():
    __config__ = [("regex","bool","Eintraege aus der Suchdatei als regulaere Ausdruecke behandeln", "False"),
                  ("quality", """480p;720p;1080p""", "480p, 720p oder 1080p", "720p"),
                  ("file", "str", "Datei mit Seriennamen", "/config/Serien.txt"),
                  ("rejectlist", "str", "Titel ablehnen mit (; getrennt)", "XviD;Subbed;NCIS.New.Orleans;NCIS.Los.Angeles;LEGO"),
                  ("language", """DEUTSCH;ENGLISCH""", "Sprache", "DEUTSCH"),
                  ("interval", "int", "Interval", "15"),
                  ("hoster", """ul;so;fm;cz;alle""", "ul.to, filemonkey, cloudzer, share-online oder alle", "ul"),
                  ("pushbulletapi","str","Your Pushbullet-API key","o.kfJEpgOLWs4a9htnBzI29d9vEaRieFZj")]

    MIN_CHECK_INTERVAL = 2 * 60 #2minutes

    def activate(self):
        self.periodical.start(self.config.get('interval') * 60)

    def periodical_task(self):
        feed = feedparser.parse('http://serienjunkies.org/xml/feeds/episoden.xml')
        self.pattern = "|".join(getSeriesList(self.config.get("file"))).lower()
        reject = self.config.get("rejectlist").replace(";","|").lower() if len(self.config.get("rejectlist")) > 0 else "^unmatchable$"
        self.quality = self.config.get("quality")
        self.hoster = self.config.get("hoster")
        if self.hoster == "alle":
            self.hoster = "."
        self.added_items = []
        
        for post in feed.entries:
            link = post.link
            title = post.title
            
            if self.config.get("regex"):
                m = re.search(self.pattern,title.lower())
                if not m and not "720p" in title and not "1080p" in title:
                    m = re.search(self.pattern.replace("480p","."),title.lower())
                    self.quality = "480p"
                if m:
                    if "720p" in title.lower(): self.quality = "720p"
                    if "1080p" in title.lower(): self.quality = "1080p"
                    m = re.search(reject,title.lower())
                    if m:
                        self.log_debug("Abgelehnt: " + title)
                        continue
                    title = re.sub('\[.*\] ', '', post.title)
                    self.range_checkr(link,title)
                                
            else:
                if self.config.get("quality") != '480p':
                    m = re.search(self.pattern,title.lower())
                    if m:
                        if self.config.get("language") in title:
                            mm = re.search(self.quality,title.lower())
                            if mm:
                                mmm = re.search(reject,title.lower())
                                if mmm:
                                    self.log_debug("Abgelehnt: " + title)
                                    continue
                                title = re.sub('\[.*\] ', '', post.title)
                                self.range_checkr(link,title)
        
                else:
                    m = re.search(self.pattern,title.lower())
                    if m:
                        if self.config.get("language") in title:
                            if "720p" in title.lower() or "1080p" in title.lower():
                                continue
                            mm = re.search(reject,title.lower())
                            if mm:
                                self.log_debug("Abgelehnt: " + title)
                                continue
                            title = re.sub('\[.*\] ', '', post.title)
                            self.range_checkr(link,title)

        if len(self.config.get('pushbulletapi')) > 2:
            notifyPushbulletSJ(self.config.get("pushbulletapi"),self.added_items) if len(self.added_items) > 0 else True
                    
    def range_checkr(self, link, title):
        pattern = re.match(".*S\d{2}E\d{2}-\w?\d{2}.*", title)
        if pattern is not None:
            range0 = re.sub(r".*S\d{2}E(\d{2}-\w?\d{2}).*",r"\1", title).replace("E","")
            number1 = re.sub(r"(\d{2})-\d{2}",r"\1", range0)
            number2 = re.sub(r"\d{2}-(\d{2})",r"\1", range0)
            title_cut = re.findall(r"(.*S\d{2}E)(\d{2}-\w?\d{2})(.*)",title)
            for count in range(int(number1),(int(number2)+1)):
                NR = re.match("d\{2}", str(count))
                if NR is not None:
                    title1 = title_cut[0][0] + str(count) + ".*" + title_cut[0][-1]
                    self.range_parse(link, title1)
                else:
                    title1 = title_cut[0][0] + "0" + str(count) + ".*" + title_cut[0][-1]
                    self.range_parse(link, title1)
        else:
            self.parse_download(link, title)


    def range_parse(self,series_url, search_title):
        req_page = getURL(series_url)
        soup = BeautifulSoup(req_page)
        titles = soup.findAll(text=re.compile(search_title))
        for title in titles:
           if self.quality !='480p' and self.quality in title: 
               self.parse_download(series_url, title)
           if self.quality =='480p' and not (('.720p.' in title) or ('.1080p.' in title)):               
               self.parse_download(series_url, title)


    def parse_download(self,series_url, search_title):
        req_page = getURL(series_url)
        soup = BeautifulSoup(req_page)
        title = soup.find(text=re.compile(search_title))
        if title:
            items = []
            links = title.parent.parent.findAll('a')
            for link in links:
                url = link['href']
                pattern = '.*%s_.*' % self.hoster
                if re.match(pattern, url):
                    items.append(url)
            self.send_package(title,items) if len(items) > 0 else True

    def send_package(self, title, link):
        try:
            storage = self.db.retrieve(title)
        except Exception:
            self.log_debug("db.retrieve got exception, title: %s" % title)                 
        if storage == 'downloaded':
            self.log_debug(title + " already downloaded")
        else:
            self.log_info("NEW EPISODE: " + title)
            self.db.store(title, 'downloaded')
        write_crawljob_file(title, title, link,
                                config.crawljob_directory)
        self.added_items.append(title.encode("utf-8"))

