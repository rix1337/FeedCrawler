# -*- coding: utf-8 -*-
# RSScrawler - Version 1.4.0
# Projekt von https://github.com/rix1337
# Enthaltener Code
# https://github.com/dmitryint (im Auftrag von https://github.com/rix1337)
# https://github.com/zapp-brannigan/own-pyload-plugins/blob/master/hooks/MovieblogFeed.py
# https://github.com/Gutz-Pilz/pyLoad-stuff/blob/master/SJ.py
# https://github.com/bharnett/Infringer/blob/master/LinkRetrieve.py
# Beschreibung:
# RSScrawler durchsucht MB/SJ nach in .txt Listen hinterlegten Titeln und reicht diese im .crawljob Format an JDownloader weiter.

"""RSScrawler.

Nutzung:
  RSScrawler.py [--testlauf]
                [--jd-pfad=<JDPATH>]
                [--log-level=<LOGLEVEL>]

Startparameter:
  --testlauf                Einmalige Ausführung von RSScrawler
  --jd-pfad=<JDPFAD>        Legt den Pfad von JDownloader vorab fest (nützlich bei headless-Systemen)
  --log-level=<LOGLEVEL>    Legt fest, wie genau geloggt wird (CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET )
"""

version = "v.1.4.0"

from docopt import docopt
from lxml import html
import requests
import feedparser
import re
import urllib
import urllib2
import codecs
import base64
from BeautifulSoup import BeautifulSoup
import pycurl
import time
import sys
import signal
import logging
import os
import errno

from rssconfig import RssConfig
from rssdb import RssDb
from timer import RepeatableTimer
import common

try:
    import simplejson as json
except ImportError:
    import json

def write_crawljob_file(package_name, folder_name, link_text, crawljob_dir):
    crawljob_file = crawljob_dir + '/%s.crawljob' % unicode(
        re.sub('[^\w\s\.-]', '', package_name.replace(' ', '')).strip().lower()
    )
    try:
        file = open(crawljob_file, 'w')
        file.write('enabled=TRUE\n')
        file.write('autoStart=TRUE\n')
        file.write('extractAfterDownload=TRUE\n')
        file.write('forcedStart=TRUE\n')
        file.write('autoConfirm=TRUE\n')
        file.write('downloadFolder=%s\n' % folder_name)
        file.write('packageName=%s\n' % package_name.replace(' ', ''))
        file.write('text=%s\n' % link_text[0])
        file.close()
        return True
    except UnicodeEncodeError as e:
        file.close()
        logging.error("While writing in the file: %s the error occurred: %s" %(crawljob_file, e.message))
        if os.path.isfile(crawljob_file):
            logging.info("Removing broken file: %s" % crawljob_file)
            os.remove(crawljob_file)
        return False

# MovieBlog
def notifyPushbulletMB(apikey,text):
    if apikey == "0" or apikey == "":
        return
    postData = '{"type":"note", "title":"RSScrawler:", "body":"%s"}' %" ### ".join(text).encode("utf-8")
    c = pycurl.Curl()
    c.setopt(pycurl.WRITEFUNCTION, lambda x: None)
    c.setopt(pycurl.URL, 'https://api.pushbullet.com/v2/pushes')
    c.setopt(pycurl.HTTPHEADER, ['Content-Type: application/json'])
    c.setopt(pycurl.USERPWD, apikey.encode('utf-8'))
    c.setopt(pycurl.POST, 1)
    c.setopt(pycurl.POSTFIELDS, postData)
    c.perform()


def _mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            logging.error("Cannot create directory: %s" % path)
            raise


def _restart_timer(func):
    def wrapper(self):
        func(self)
        if self._periodical_active:
            self.periodical.cancel()
            self.periodical.start()

    return wrapper

class MovieblogFeed():
    FEED_URL = "http://www.movie-blog.org/feed/"
    SUBSTITUTE = "[&#\s/]"
    _INTERNAL_NAME='MB'

    def __init__(self):
        self.config = RssConfig(self._INTERNAL_NAME)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.db = RssDb(os.path.join(os.path.dirname(__file__), "Einstellungen/Downloads/MB_Downloads.db"))
        self.filme = os.path.join(os.path.dirname(__file__), 'Einstellungen/Listen/MB_Filme.txt')
        self.staffeln = os.path.join(os.path.dirname(__file__), 'Einstellungen/Listen/MB_Staffeln.txt')
        self._hosters_pattern = rsscrawler.get('hoster').replace(';','|')
        self._periodical_active = False
        self.periodical = RepeatableTimer(
            int(rsscrawler.get('interval')) * 60,
            self.periodical_task
        )
        self.dictWithNamesAndLinks = {}

    def activate(self):
        self._periodical_active = True
        self.periodical.start()
        return self

    def readInput(self, file):
        if not os.path.isfile(file):
            open(file, "a").close()
            placeholder = open(file, 'w')
            placeholder.write('RSSCRAWLER VON RIX - Ein Titel Pro Zeile - BEACHTE DIE README.md')
            placeholder.close()
        try:
            f = codecs.open(file, "rb")
            return f.read().splitlines()
        except:
            self.log_error("Inputfile not found")

    def getPatterns(self, patterns, quality, rg, sf):
        return {line: (quality, rg, sf) for line in patterns}

    def searchLinks(self, feed):
        ignore = "|".join(["\.%s\." % p for p in self.config.get("ignore").lower().split(',')
                           if not self.config.get('crawl3d') or p != '3d']) \
            if not self.config.get("ignore") == "" else "^unmatchable$"
        for key in self.allInfos:
            s = re.sub(self.SUBSTITUTE,".",key).lower()
            for post in feed.entries:
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

                    if '.3d.' in post.title.lower():
                        if self.config.get('crawl3d') and ("1080p" in post.title.lower() or "1080i" in post.title.lower()):
                            found = True
                        else:
                            continue
                    else:
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

                        if self.allInfos[key][2]:
                            # If all True, then found = True
                            found = all([word in post.title.lower() for word in self.allInfos[key][2]])

                        if found:
                            try:
                                episode = re.search(r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*',post.title.lower()).group(1)
                                if "repack" in post.title.lower():
                                    episode = episode + "-repack"
                                self.log_debug("TV-Series detected, will shorten its name to [%s]" %episode)
                                yield (episode, [post.link], key)
                            except:
                                yield (post.title, [post.link], key)


    def _get_download_links(self, url, hosters_pattern=None):
        tree = html.fromstring(requests.get(url).content)
        xpath = '//*[@id="content"]/span/div/div[2]//strong[contains(text(),"Download:") or contains(text(),"Mirror #")]/following-sibling::a[1]'
        return [common.get_first(link.xpath('./@href')) for link in tree.xpath(xpath) if hosters_pattern is None or re.search(hosters_pattern, link.text, flags=re.IGNORECASE)]

    @_restart_timer
    def periodical_task(self):
        urls = []
        text = []

        dl = {key:('.*', '.*', ('.dl.',)) for key in self.db.get_patterns('notdl')}

        self.allInfos = dict(
            set({key: dl[key] if key in dl else value for (key, value) in self.getPatterns(
                    self.readInput(self.filme),
                    self.config.get('quality'),
                    '.*',
                    None
                ).items()}.items()
            ) |
            set(self.getPatterns(
                    self.readInput(self.staffeln),
                    self.config.get('seasonsquality'),
                    '.*',
                    ('.complete.','.' + self.config.get('seasonssource') + '.')
            ).items() if self.config.get('crawlseasons') else [])
        )

        if self.config.get("historical"):
            for xline in self.allInfos.keys():
                if len(xline) > 0 and not xline.startswith("#"):
                    xn = xline.split(",")[0].replace(".", " ").replace(" ", "+")
                    urls.append('http://www.movie-blog.org/search/%s/feed/rss2/' %xn)
        else:
            urls.append(self.FEED_URL)

        for url in urls:
            for (key, value, pattern) in self.searchLinks(feedparser.parse(url)):
                if self.db.retrieve(key) == 'added' or self.db.retrieve(key) == 'notdl':
                    self.log_debug("[%s] wurde bereits hinzugefügt" % key)
                else:
                    self.db.store(
                        key,
                        'notdl' if self.config.get('enforcedl') and '.dl.' not in key.lower() else 'added',
                        pattern
                    )
                    self.log_info("RSScrawler: " + key)
                    if not os.path.exists(rsscrawler.get("jdownloader") + '/folderwatch/rsscrawler.' + version + '.readme-rix.crawljob'):
                        if not os.path.exists(rsscrawler.get("jdownloader") + '/folderwatch/added/rsscrawler.' + version + '.readme-rix.crawljob'):
                            write_crawljob_file("rsscrawler." + version + ".readme-rix", "RSSCrawler." + version + ".README-RiX", ["https://raw.githubusercontent.com/rix1337/RSScrawler/master/README.md"], rsscrawler.get("jdownloader") + "/folderwatch")
                    download_link = [common.get_first(self._get_download_links(value[0], self._hosters_pattern))]
                    if any(download_link):
                        write_crawljob_file(
                            key,
                            key,
                            download_link,
                            rsscrawler.get("jdownloader") + "/folderwatch"
                        ) and text.append(key)
        if len(text) > 0:
            notifyPushbulletMB(rsscrawler.get("pushbulletapi"),text)

# Serienjunkies
def getSeriesList(file):
    if not os.path.isfile(file):
        open(file, "a").close()
        placeholder = open(file, 'w')
        placeholder.write('RSSCRAWLER VON RIX - Ein Titel Pro Zeile - BEACHTE DIE README.md')
        placeholder.close()
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
        logging.error("STOPPED, invalid character in list!")
    except IOError:
        logging.error("STOPPED, list not found!")
    except Exception, e:
        logging.error("Unknown error: %s" %e)

def getRegexSeriesList(file):
    if not os.path.isfile(file):
        open(file, "a").close()
        placeholder = open(file, 'w')
        placeholder.write('RSSCRAWLER VON RIX - Ein Titel Pro Zeile - BEACHTE DAS REGEX FORMAT UND DIE README.md')
        placeholder.close()
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
        logging.error("STOPPED, invalid character in list!")
    except IOError:
        logging.error("STOPPED, list not found!")
    except Exception, e:
        logging.error("Unknown error: %s" %e)

def notifyPushbulletSJ(api='', msg=''):
    data = urllib.urlencode({
        'type': 'note',
        'title': 'RSScrawler:',
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


def getURL(url):
    try:
        req = urllib2.Request(
            url,
            None,
            {'User-agent' : 'Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5'}
        )
        return urllib2.urlopen(req).read()
    except urllib2.HTTPError as e:
        logging.debug('During query execution we got an exception: Code: %s Reason: %s' % (e.code, e.reason))
        return ''
    except urllib2.URLError as e:
        logging.debug('During query execution we got an exception: Reason: %s' %  e.reason)
        return ''

class SJ():
    MIN_CHECK_INTERVAL = 2 * 60 #2minutes
    _INTERNAL_NAME = 'SJ'

    def __init__(self):
        self.config = RssConfig(self._INTERNAL_NAME)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.db = RssDb(os.path.join(os.path.dirname(__file__), "Einstellungen/Downloads/SJ_Downloads.db"))
        self.serien = os.path.join(os.path.dirname(__file__), 'Einstellungen/Listen/SJ_Serien.txt')
        self._periodical_active = False
        self.periodical = RepeatableTimer(
            int(rsscrawler.get('interval')) * 60,
            self.periodical_task
        )

    def activate(self):
        self._periodical_active = True
        self.periodical.start()

    @_restart_timer
    def periodical_task(self):
        feed = feedparser.parse('http://serienjunkies.org/xml/feeds/episoden.xml')
        self.pattern = "|".join(getSeriesList(os.path.join(os.path.dirname(__file__), "Einstellungen/Listen/SJ_Serien.txt"))).lower()
        reject = self.config.get("rejectlist").replace(";","|").lower() if len(self.config.get("rejectlist")) > 0 else "^unmatchable$"
        self.quality = self.config.get("quality")
        self.hoster = rsscrawler.get("hoster")
        if self.hoster == "Uploaded":
            self.hoster = "ul"
        if self.hoster == "Share-Online":
            self.hoster = "so"
        self.added_items = []

        for post in feed.entries:
            link = post.link
            title = post.title

            if self.config.get("quality") != '480p':
                m = re.search(self.pattern,title.lower())
                if m:
                    if '[DEUTSCH]' in title:
                        mm = re.search(self.quality,title.lower())
                        if mm:
                            mmm = re.search(reject,title.lower())
                            if mmm:
                                self.log_debug("Rejected: " + title)
                                continue
                            title = re.sub('\[.*\] ', '', post.title)
                            self.range_checkr(link,title)

                else:
                    m = re.search(self.pattern,title.lower())
                    if m:
                        if '[DEUTSCH]' in title:
                            if "720p" in title.lower() or "1080p" in title.lower():
                                continue
                            mm = re.search(reject,title.lower())
                            if mm:
                                self.log_debug("Rejected: " + title)
                                continue
                            title = re.sub('\[.*\] ', '', post.title)
                            self.range_checkr(link,title)

        if len(rsscrawler.get('pushbulletapi')) > 2:
            notifyPushbulletSJ(rsscrawler.get("pushbulletapi"),self.added_items) if len(self.added_items) > 0 else True

    def range_checkr(self, link, title):
        pattern = re.match(".*S\d{2}E\d{2}-\w?\d{2}.*", title)
        if pattern is not None:
            range0 = re.sub(r".*S\d{2}E(\d{2}-\w?\d{2}).*",r"\1", title).replace("E","")
            number1 = re.sub(r"(\d{2})-\d{2}",r"\1", range0)
            number2 = re.sub(r"\d{2}-(\d{2})",r"\1", range0)
            title_cut = re.findall(r"(.*S\d{2}E)(\d{2}-\w?\d{2})(.*)",title)
            try:
                for count in range(int(number1),(int(number2)+1)):
                    NR = re.match("d\{2}", str(count))
                    if NR is not None:
                        title1 = title_cut[0][0] + str(count) + ".*" + title_cut[0][-1]
                        self.range_parse(link, title1)
                    else:
                        title1 = title_cut[0][0] + "0" + str(count) + ".*" + title_cut[0][-1]
                        self.range_parse(link, title1)
            except ValueError as e:
                logging.error("Raised ValueError exception: %s" %e.message)
        else:
            self.parse_download(link, title)

    def range_parse(self,series_url, search_title):
        req_page = getURL(series_url)
        soup = BeautifulSoup(req_page)

        try:
            titles = soup.findAll(text=re.compile(search_title))
            for title in titles:
               if self.quality !='480p' and self.quality in title:
                   self.parse_download(series_url, title)
               if self.quality =='480p' and not (('.720p.' in title) or ('.1080p.' in title)):
                   self.parse_download(series_url, title)
        except re.error as e:
            self.log_error('sre_constants.error: %s' % e)


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
        except Exception as e:
            self.log_debug("db.retrieve got exception: %s, title: %s" % (e,title))
        if storage == 'downloaded':
            self.log_debug(title + " wurde bereits hinzugefügt")
        else:
            self.log_info("RSScrawler: " + title)
            self.db.store(title, 'downloaded')
            if not os.path.exists(rsscrawler.get("jdownloader") + '/folderwatch/rsscrawler.' + version + '.readme-rix.crawljob'):
                if not os.path.exists(rsscrawler.get("jdownloader") + '/folderwatch/added/rsscrawler.' + version + '.readme-rix.crawljob'):
                    write_crawljob_file("rsscrawler." + version + ".readme-rix", "RSSCrawler." + version + ".README-RiX", ["https://raw.githubusercontent.com/rix1337/RSScrawler/master/README.md"], rsscrawler.get("jdownloader") + "/folderwatch")
            write_crawljob_file(title, title, link,
                                rsscrawler.get("jdownloader") + "/folderwatch") and self.added_items.append(title.encode("utf-8"))

class SJregex():
    MIN_CHECK_INTERVAL = 2 * 60 #2minutes
    _INTERNAL_NAME = 'SJ'

    def __init__(self):
        self.config = RssConfig(self._INTERNAL_NAME)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        if self.config.get("regex"):
            self.db = RssDb(os.path.join(os.path.dirname(__file__), "Einstellungen/Downloads/SJ_Downloads.db"))
            self._periodical_active = False
            self.periodical = RepeatableTimer(
                int(rsscrawler.get('interval')) * 60,
                self.periodical_task
            )

    def activate(self):
        self._periodical_active = True
        self.periodical.start()

    @_restart_timer
    def periodical_task(self):
        feed = feedparser.parse('http://serienjunkies.org/xml/feeds/episoden.xml')
        self.pattern = "|".join(getRegexSeriesList(os.path.join(os.path.dirname(__file__), "Einstellungen/Listen/SJ_Serien_Regex.txt"))).lower()
        reject = self.config.get("rejectlist").replace(";","|").lower() if len(self.config.get("rejectlist")) > 0 else "^unmatchable$"
        self.quality = self.config.get("quality")
        self.hoster = rsscrawler.get("hoster")
        if self.hoster == "Uploaded":
            self.hoster = "ul"
        if self.hoster == "Share-Online":
            self.hoster = "so"
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
                        self.log_debug("Regex did not Reject: " + title)
                    title = re.sub('\[.*\] ', '', post.title)
                    self.range_checkr(link,title)

            else:
                continue
            
        if len(rsscrawler.get('pushbulletapi')) > 2:
            notifyPushbulletSJ(rsscrawler.get("pushbulletapi"),self.added_items) if len(self.added_items) > 0 else True

    def range_checkr(self, link, title):
        pattern = re.match(".*S\d{2}E\d{2}-\w?\d{2}.*", title)
        if pattern is not None:
            range0 = re.sub(r".*S\d{2}E(\d{2}-\w?\d{2}).*",r"\1", title).replace("E","")
            number1 = re.sub(r"(\d{2})-\d{2}",r"\1", range0)
            number2 = re.sub(r"\d{2}-(\d{2})",r"\1", range0)
            title_cut = re.findall(r"(.*S\d{2}E)(\d{2}-\w?\d{2})(.*)",title)
            try:
                for count in range(int(number1),(int(number2)+1)):
                    NR = re.match("d\{2}", str(count))
                    if NR is not None:
                        title1 = title_cut[0][0] + str(count) + ".*" + title_cut[0][-1]
                        self.range_parse(link, title1)
                    else:
                        title1 = title_cut[0][0] + "0" + str(count) + ".*" + title_cut[0][-1]
                        self.range_parse(link, title1)
            except ValueError as e:
                logging.error("Raised ValueError exception: %s" %e.message)
        else:
            self.parse_download(link, title)

    def range_parse(self,series_url, search_title):
        req_page = getURL(series_url)
        soup = BeautifulSoup(req_page)

        try:
            titles = soup.findAll(text=re.compile(search_title))
            for title in titles:
               if self.quality !='480p' and self.quality in title:
                   self.parse_download(series_url, title)
               if self.quality =='480p' and not (('.720p.' in title) or ('.1080p.' in title)):
                   self.parse_download(series_url, title)
        except re.error as e:
            self.log_error('sre_constants.error: %s' % e)


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
        except Exception as e:
            self.log_debug("db.retrieve got exception: %s, title: %s" % (e,title))
        if storage == 'downloaded':
            self.log_debug(title + " wurde bereits hinzugefügt")
        else:
            self.log_info("RSScrawler: " + title)
            self.db.store(title, 'downloaded')
            if not os.path.exists(rsscrawler.get("jdownloader") + '/folderwatch/rsscrawler.' + version + '.readme-rix.crawljob'):
                if not os.path.exists(rsscrawler.get("jdownloader") + '/folderwatch/added/rsscrawler.' + version + '.readme-rix.crawljob'):
                    write_crawljob_file("rsscrawler." + version + ".readme-rix", "RSSCrawler." + version + ".README-RiX", ["https://raw.githubusercontent.com/rix1337/RSScrawler/master/README.md"], rsscrawler.get("jdownloader") + "/folderwatch")
            write_crawljob_file(title, title, link,
                                rsscrawler.get("jdownloader") + "/folderwatch") and self.added_items.append(title.encode("utf-8"))

if __name__ == "__main__":
    arguments = docopt(__doc__, version='RSScrawler')

    if arguments['--log-level']:
        logging.basicConfig(
            filename=os.path.join(os.path.dirname(__file__), 'RSScrawler.log'), format='%(asctime)s %(message)s', level=logging.__dict__[arguments['--log-level']] if arguments['--log-level'] in logging.__dict__ else logging.INFO
        )
        console = logging.StreamHandler()
        console.setLevel(logging.__dict__[arguments['--log-level']] if arguments['--log-level'] in logging.__dict__ else logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(message)s')
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)

    # This mutes 'Starting new HTTP connection (1)' from info log
    logging.getLogger("requests").setLevel(logging.WARNING)
    #  Add info to the console
    print("RSScrawler " + version + " von rix")
    print("Originalseite: https://github.com/rix1337/RSScrawler/")
    
    # Erstelle Einstellungen Ordner
    if not os.path.exists(os.path.join(os.path.dirname(__file__), 'Einstellungen')):
        _mkdir_p(os.path.join(os.path.dirname(__file__), 'Einstellungen'))
    if not os.path.exists(os.path.join(os.path.dirname(__file__), 'Einstellungen/Downloads')):
        _mkdir_p(os.path.join(os.path.dirname(__file__), 'Einstellungen/Downloads'))
    if not os.path.exists(os.path.join(os.path.dirname(__file__), 'Einstellungen/Listen')):
        _mkdir_p(os.path.join(os.path.dirname(__file__), 'Einstellungen/Listen'))
    if not os.path.isfile(os.path.join(os.path.dirname(__file__), 'Einstellungen/Listen/MB_Filme.txt')):
        open(os.path.join(os.path.dirname(__file__), 'Einstellungen/Listen/MB_Filme.txt'), "a").close()
        placeholder = open(os.path.join(os.path.dirname(__file__), 'Einstellungen/Listen/MB_Filme.txt'), 'w')
        placeholder.write('RSSCRAWLER VON RIX - Ein Titel Pro Zeile - BEACHTE DIE README.md')
        placeholder.close()
    if not os.path.isfile(os.path.join(os.path.dirname(__file__), 'Einstellungen/Listen/MB_Staffeln.txt')):
        open(os.path.join(os.path.dirname(__file__), 'Einstellungen/Listen/MB_Staffeln.txt'), "a").close()
        placeholder = open(os.path.join(os.path.dirname(__file__), 'Einstellungen/Listen/MB_Staffeln.txt'), 'w')
        placeholder.write('RSSCRAWLER VON RIX - Ein Titel Pro Zeile - BEACHTE DIE README.md')
        placeholder.close()
    if not os.path.isfile(os.path.join(os.path.dirname(__file__), 'Einstellungen/Listen/SJ_Serien.txt')):
        open(os.path.join(os.path.dirname(__file__), 'Einstellungen/Listen/SJ_Serien.txt'), "a").close()
        placeholder = open(os.path.join(os.path.dirname(__file__), 'Einstellungen/Listen/SJ_Serien.txt'), 'w')
        placeholder.write('RSSCRAWLER VON RIX - Ein Titel Pro Zeile - BEACHTE DIE README.md')
        placeholder.close()
    if not os.path.isfile(os.path.join(os.path.dirname(__file__), 'Einstellungen/Listen/SJ_Serien_Regex.txt')):
        open(os.path.join(os.path.dirname(__file__), 'Einstellungen/Listen/SJ_Serien_Regex.txt'), "a").close()
        placeholder = open(os.path.join(os.path.dirname(__file__), 'Einstellungen/Listen/SJ_Serien_Regex.txt'), 'w')
        placeholder.write('RSSCRAWLER VON RIX - Ein Titel Pro Zeile - BEACHTE DAS REGEX FORMAT UND DIE README.md')
        placeholder.close()
            
    # Setze relativen Dateinamen der Einstellungsdatei    
    einstellungen = os.path.join(os.path.dirname(__file__), 'Einstellungen/RSScrawler.ini')
    # Erstelle RSScrawler.ini, wenn nicht bereits vorhanden
    if not arguments['--jd-pfad']:
        if not os.path.exists(einstellungen):
            open(einstellungen, "a").close()
            einsteller = open(einstellungen, 'w')
            einsteller.write('# Hier werden sämtliche Einstellungen von RSScrawler hinterlegt\n# Dieses Script funktioniert nur sinnvoll, wenn Folder Watch im JDownloader aktiviert ist.\n# Es muss weiterhin unten der richtige JDownloader Pfad gesetzt werden!\n# Zur automatischen Captcha-Lösung empfehle ich:\n# https://www.9kw.eu/register_87296.html\n# Des weiteren empfehle ich einen Premium-Account bei Uploaded:\n# http://ul.to/ref/14406819\n\n# Diese allgemeinen Einstellungen müssen korrekt sein:\n[RSScrawler]\n# Dieser Pfad muss das exakte Verzeichnis des JDownloaders sein, sonst funktioniert das Script nicht!\njdownloader = Muss unbedingt vergeben werden!\n# Das Suchintervall in Minuten sollte nicht zu niedrig angesetzt werden um keinen Ban zu riskieren\ninterval = 10\n# Um über hinzugefügte Releases informiert zu werden hier den Pushbullet API-Key eintragen\npushbulletapi = \n# Hier den gewünschten Hoster eintragen (Uploaded oder Share-Online)\nhoster = Uploaded\n\n# Dieser Bereich ist für die Suche auf Movie-Blog.org zuständig:\n[MB]\n# Die Qualität, nach der Gesucht wird (1080p, 720p oder 480p)\nquality = 720p\n# Releases mit diesen Begriffen werden nicht hinzugefügt (durch Kommas getrennt)\nignore = ts,cam,subbed,xvid,dvdr,untouched,remux,pal,md,ac3md,mic,xxx,hou\n# Wenn aktiviert wird die MB-Suchfunktion genutzt (langsamer), da der Feed nur wenige Stunden abbildet\nhistorical = True\n# Wenn aktiviert sucht das Script nach 3D Releases (in 1080p), unabhängig von der oben gesetzten Qualität\ncrawl3d = False\n# Wenn aktiviert, erzwingt das Script zweisprachige Releases. Sollte ein Release allen Regeln entsprechen, aber kein\n# DL-Tag enthalten, wird es hinzugefügt. Ab diesem Zeitpunkt gilt aber die Quality-Regel nicht mehr für den entsprechenden\n# Film. Solange ein Release *DL* im Titel trägt wird es hinzugefügt, solange der Film auf der MB_Filme Liste steht. Diese\n# Option empfiehlt sich nur bei ausreichender Bandbreite, wenn man bspw. Filme in 720p und DL sammeln möchte.\nenforcedl = False\n# Komplette Staffeln von Serien landen zuverlässiger auf MB als auf SJ. Diese Option erlaubt die entsprechende Suche\ncrawlseasons = True\n# Die Qualität, nach der Staffeln gesucht werden (1080p, 720p oder 480p)\nseasonsquality = 720p\n# Der Staffel-Releasetyp nach dem gesucht wird\nseasonssource = bluray\n\n# Dieser Bereich ist für die Suche auf Serienjunkies.org zuständig:\n[SJ]\n# Die Qualität, nach der Gesucht wird (1080p, 720p oder 480p)\nquality = 720p\n# Releases mit diesen Begriffen werden nicht hinzugefügt (durch Semikola getrennt)\nrejectlist = XviD;Subbed;HDTV\n# Wenn aktiviert werden in einer zweiten Suchdatei Serien nach Regex-Regeln gesucht\nregex = True\n\n# Die Listen (MB_Filme, MB_Serien, SJ_Serien, SJ_Serien_Regex:\n# 1. MB_Filme enthält pro Zeile den Titel eines Films (Film Titel), um auf MB nach Filmen zu suchen\n# 2. MB_Serien enthält pro Zeile den Titel einer Serie (Serien Titel), um auf MB nach kompletten Staffeln zu suchen\n# 3. SJ_Serien enthält pro Zeile den Titel einer Serie (Serien Titel), um auf SJ nach Serien zu suchen\n# 4. SJ_Serien_Regex enthält pro Zeile den Titel einer Serie in einem speziellen Format, wobei die Filter ignoriert werden:\n#    Serien.Titel.*.S01.*.720p.*-GROUP sucht nach Releases der Gruppe GROUP von Staffel 1 der Serien Titel in 720p\n#    Serien.Titel.* sucht nach allen Releases von Serien Titel (nützlich, wenn man sonst HDTV aussortiert)\n#    Serien.Titel.*.DL.*.720p.* sucht nach zweisprachigen Releases in 720p von Serien Titel')
            einsteller.close()
            print('Die Einstellungsdatei wurde erstellt. Der Pfad des JDownloaders muss jetzt unbedingt in der RSScrawler.ini hinterlegt werden.')
            print('Viel Spaß! Beende RSScrawler!')
            sys.exit(0)
    else:
        if not os.path.exists(einstellungen):
            open(einstellungen, "a").close()
            einsteller = open(einstellungen, 'w')
            einsteller.write('# Hier werden sämtliche Einstellungen von RSScrawler hinterlegt\n# Dieses Script funktioniert nur sinnvoll, wenn Folder Watch im JDownloader aktiviert ist.\n# Es muss weiterhin unten der richtige JDownloader Pfad gesetzt werden!\n# Zur automatischen Captcha-Lösung empfehle ich:\n# https://www.9kw.eu/register_87296.html\n# Des weiteren empfehle ich einen Premium-Account bei Uploaded:\n# http://ul.to/ref/14406819\n\n# Diese allgemeinen Einstellungen müssen korrekt sein:\n[RSScrawler]\n# Dieser Pfad muss das exakte Verzeichnis des JDownloaders sein, sonst funktioniert das Script nicht!\njdownloader = ' + arguments['--jd-pfad'] + '\n# Das Suchintervall in Minuten sollte nicht zu niedrig angesetzt werden um keinen Ban zu riskieren\ninterval = 10\n# Um über hinzugefügte Releases informiert zu werden hier den Pushbullet API-Key eintragen\npushbulletapi = \n# Hier den gewünschten Hoster eintragen (Uploaded oder Share-Online)\nhoster = Uploaded\n\n# Dieser Bereich ist für die Suche auf Movie-Blog.org zuständig:\n[MB]\n# Die Qualität, nach der Gesucht wird (1080p, 720p oder 480p)\nquality = 720p\n# Releases mit diesen Begriffen werden nicht hinzugefügt (durch Kommas getrennt)\nignore = ts,cam,subbed,xvid,dvdr,untouched,remux,pal,md,ac3md,mic,xxx,hou\n# Wenn aktiviert wird die MB-Suchfunktion genutzt (langsamer), da der Feed nur wenige Stunden abbildet\nhistorical = True\n# Wenn aktiviert sucht das Script nach 3D Releases (in 1080p), unabhängig von der oben gesetzten Qualität\ncrawl3d = False\n# Wenn aktiviert, erzwingt das Script zweisprachige Releases. Sollte ein Release allen Regeln entsprechen, aber kein\n# DL-Tag enthalten, wird es hinzugefügt. Ab diesem Zeitpunkt gilt aber die Quality-Regel nicht mehr für den entsprechenden\n# Film. Solange ein Release *DL* im Titel trägt wird es hinzugefügt, solange der Film auf der MB_Filme Liste steht. Diese\n# Option empfiehlt sich nur bei ausreichender Bandbreite, wenn man bspw. Filme in 720p und DL sammeln möchte.\nenforcedl = False\n# Komplette Staffeln von Serien landen zuverlässiger auf MB als auf SJ. Diese Option erlaubt die entsprechende Suche\ncrawlseasons = True\n# Die Qualität, nach der Staffeln gesucht werden (1080p, 720p oder 480p)\nseasonsquality = 720p\n# Der Staffel-Releasetyp nach dem gesucht wird\nseasonssource = bluray\n\n# Dieser Bereich ist für die Suche auf Serienjunkies.org zuständig:\n[SJ]\n# Die Qualität, nach der Gesucht wird (1080p, 720p oder 480p)\nquality = 720p\n# Releases mit diesen Begriffen werden nicht hinzugefügt (durch Semikola getrennt)\nrejectlist = XviD;Subbed;HDTV\n# Wenn aktiviert werden in einer zweiten Suchdatei Serien nach Regex-Regeln gesucht\nregex = True\n\n# Die Listen (MB_Filme, MB_Serien, SJ_Serien, SJ_Serien_Regex:\n# 1. MB_Filme enthält pro Zeile den Titel eines Films (Film Titel), um auf MB nach Filmen zu suchen\n# 2. MB_Serien enthält pro Zeile den Titel einer Serie (Serien Titel), um auf MB nach kompletten Staffeln zu suchen\n# 3. SJ_Serien enthält pro Zeile den Titel einer Serie (Serien Titel), um auf SJ nach Serien zu suchen\n# 4. SJ_Serien_Regex enthält pro Zeile den Titel einer Serie in einem speziellen Format, wobei die Filter ignoriert werden:\n#    Serien.Titel.*.S01.*.720p.*-GROUP sucht nach Releases der Gruppe GROUP von Staffel 1 der Serien Titel in 720p\n#    Serien.Titel.* sucht nach allen Releases von Serien Titel (nützlich, wenn man sonst HDTV aussortiert)\n#    Serien.Titel.*.DL.*.720p.* sucht nach zweisprachigen Releases in 720p von Serien Titel')
            einsteller.close()
            print('Die Einstellungsdatei wurde erstellt. Der Pfad des JDownloaders muss jetzt unbedingt in der RSScrawler.ini hinterlegt werden.')
            print('Viel Spaß! Beende RSScrawler!')
            sys.exit(0)
    # Definiere die allgemeinen Einstellungen global
    rsscrawler = RssConfig('RSScrawler')
    
    # Abbrechen, wenn JDownloader Pfad nicht vergeben wurde
    if rsscrawler.get('jdownloader') == 'Muss unbedingt vergeben werden!':
        print('Der Pfad des JDownloaders muss unbedingt in der RSScrawler.ini hinterlegt werden.')
        print('Beende RSScrawler!')
        sys.exit(0)
        
    # Abbrechen, wenn JDownloader Pfad nicht existiert
    if not os.path.exists(rsscrawler.get('jdownloader')):
        print('Der Pfad des JDownloaders existiert nicht.')
        print('Beende RSScrawler!')
        sys.exit(0)
        
    pool = [
        MovieblogFeed(),
        SJ(),
        SJregex(),
    ]

    def signal_handler(signal, frame):
        list([el.periodical.cancel() for el in pool])
        print('Beende...')
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
    print('Drücke Strg+C zum Beenden')

    for el in pool:
        if not arguments['--testlauf']:
            el.activate()
        el.periodical_task()

    if not arguments['--testlauf']:
        signal.pause()
