# -*- coding: utf-8 -*-
# Main code by https://github.com/dmitryint commissioned by https://github.com/rix1337
# Version 0.6.3
# Known Bugs:
# -Currently, if a Site spawns a 404 Error the script will crash.
# This project relies heavily on these three projects:
# https://github.com/zapp-brannigan/own-pyload-plugins/blob/master/hooks/MovieblogFeed.py
# https://github.com/Gutz-Pilz/pyLoad-stuff/blob/master/SJ.py
# https://github.com/bharnett/Infringer/blob/master/LinkRetrieve.py
# Description:
# This script scrapes MB/SJ for titles stored in .txt files and passes them on to JDownloader via the .crawljob format

"""RSScrawler.

Usage:
  RSScrawler.py [--ontime]
                [--log-level=<LOGLEVEL>]

Options:
  --ontime                  Run once and exit
  --log-level=<LOGLEVEL>    Level which program should log messages (eg. CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET )
"""

# Requires PyCurl, Feedparser, BeautifulSoup, docopt
from rssconfig import RssConfig
from rssdb import RssDb
from timer import RepeatableTimer
from docopt import docopt
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

try:
    import simplejson as json
except ImportError:
    import json

# Adjust all settings below!
# If your Lists are blank, all links from MB/SJ will be crawled!
# Set the lists up before starting this script for the first time.

# MB List items are made up of lines containing: Title,Resolution,ReleaseGroup,
# Example: Funny Movie,720p,GR0UP,
# The file is invalid if one comma is missing!
# Leaving Resolution or Release Group blank is also valid
# The database file prevents duplicate crawljobs

# SJ List items are made up of lines containing: Title
# Example: Funny TV-Show
# The database file prevents duplicate crawljobs

# JDownloader

# crawljobs need to be placed in the folderwatch subdir of JDownloader
# Enable the Watch-Folder feature (experimental) for links to be picked up automatically

def write_crawljob_file(package_name, folder_name, link_text, crawljob_dir):
    crawljob_file = crawljob_dir + '/%s.crawljob' % unicode(
        re.sub('[^\w\s\.-]', '', package_name.replace(' ', '')).strip().lower()
    )

    file = open(crawljob_file, 'w')
    file.write('enabled=TRUE\n')
    file.write('autoStart=TRUE\n')
    file.write('extractAfterDownload=TRUE\n')
    file.write('forcedStart=TRUE\n')
    file.write('autoConfirm=TRUE\n')
    file.write('downloadFolder=%s\n' % folder_name)
    file.write('packageName=%s\n' % package_name.replace(' ', ''))
    file.write('text=%s\n' % link_text)
    file.close()


# MovieBlog
def notifyPushbulletMB(apikey,text):
    if apikey == "0" or apikey == "":
        return
    postData = '{"type":"note", "title":"(RSScrawler) NEW RELEASE:", "body":"%s"}' %" ### ".join(text).encode("utf-8")
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
        list([_mkdir_p(os.path.dirname(self.config.get(f))) for f in ['db_file', 'patternfile']])
        _mkdir_p(self.config.get('crawljob_directory'))
        self.db = RssDb(self.config.get('db_file'))
        self._periodical_active = False
        self.periodical = RepeatableTimer(
            int(self.config.get('interval')) * 60,
            self.periodical_task
        )

    def activate(self):
        self._periodical_active = True
        self.periodical.start()
        return self

    def readInput(self):
        if not os.path.isfile(self.config.get("patternfile")):
            open(self.config.get("patternfile"), "a").close()
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

    @_restart_timer
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
                self.log_info("NEW RELEASE: " + key)
                write_crawljob_file(key, key, [self.dictWithNamesAndLinks[key][0]],
                    self.config.get("crawljob_directory"))
                text.append(key)
            else:
                self.log_debug("[%s] has already been added" %key)
        if len(text) > 0:
            notifyPushbulletMB(self.config.get("pushbulletapi"),text)

# Serienjunkies
def getSeriesList(file):
    if not os.path.isfile(file):
        open(file, "a").close()
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
        'title': '(RSScrawler) NEW RELEASE:',
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
        logging.error('During query execution we got an exception: Code: %s Reason: %s' % (e.code, e.reason))
        return ''
    except urllib2.URLError as e:
        logging.error('During query execution we got an exception: Reason: %s' %  e.reason)
        return ''

def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


class SJ():
    MIN_CHECK_INTERVAL = 2 * 60 #2minutes
    _INTERNAL_NAME = 'SJ'

    def __init__(self):
        self.config = RssConfig(self._INTERNAL_NAME)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        list([_mkdir_p(os.path.dirname(self.config.get(f))) for f in ['db_file', 'file']])
        _mkdir_p(self.config.get('crawljob_directory'))
        self.db = RssDb(self.config.get('db_file'))
        self._periodical_active = False
        self.periodical = RepeatableTimer(
            int(self.config.get('interval')) * 60,
            self.periodical_task
        )

    def activate(self):
        self._periodical_active = True
        self.periodical.start()

    @_restart_timer
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

            if str2bool(self.config.get("regex")):
                m = re.search(self.pattern,title.lower())
                if not m and not "720p" in title and not "1080p" in title:
                    m = re.search(self.pattern.replace("480p","."),title.lower())
                    self.quality = "480p"
                if m:
                    if "720p" in title.lower(): self.quality = "720p"
                    if "1080p" in title.lower(): self.quality = "1080p"
                    m = re.search(reject,title.lower())
                    if m:
                        self.log_debug("Rejected: " + title)
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
                                    self.log_debug("Rejected: " + title)
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
                                self.log_debug("Rejected: " + title)
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
            self.log_debug(title + " already downloaded")
        else:
            self.log_info("NEW RELEASE: " + title)
            self.db.store(title, 'downloaded')
            write_crawljob_file(title, title, link,
                                self.config.get('crawljob_directory'))
            self.added_items.append(title.encode("utf-8"))

if __name__ == "__main__":
    arguments = docopt(__doc__, version='RSScrawler')

    if arguments['--log-level']:
        logging.basicConfig(
            level=logging.__dict__[arguments['--log-level']] if arguments['--log-level'] in logging.__dict__ else logging.INFO
        )

    pool = [
        MovieblogFeed(),
        SJ(),
    ]

    def signal_handler(signal, frame):
        list([el.periodical.cancel() for el in pool])
        print('Bye.')
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
    print('Press Ctrl+C for exit')

    for el in pool:
        if not arguments['--ontime']:
            el.activate()
        el.periodical_task()

    if not arguments['--ontime']:
        signal.pause()
