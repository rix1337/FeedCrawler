# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337

from json import dumps, loads

import codecs
import functools
import hashlib
import pickle
import requests
from requests import RequestException
from urllib.parse import urlencode

from feedcrawler.config import CrawlerConfig
from feedcrawler.db import FeedDb


class DbFileMissingExpection(Exception):
    """Exception raised for missing dbfile path.

    Attributes:
        url -- url(s) from the request that caused the error
        message -- explanation of the error
    """

    def __init__(self, url, message="The dbfile parameter required for caching this request is missing!"):
        self.url = url
        self.message = message
        super().__init__(self.message + ", url(s): " + self.url)


def cache(func):
    """Decorator that caches a functions return values for specific arguments."""

    @functools.wraps(func)
    def cache_returned_values(*args, **kwargs):
        to_hash = ""
        dbfile = False
        for a in args:
            # The path to the db file which we will use for caching is always one of the arguments
            if isinstance(a, str) and "FeedCrawler.db" in a:
                dbfile = a
            # ToDo potentially ignore the cloudproxy_session
            to_hash += codecs.encode(pickle.dumps(a), "base64").decode()
        # This hash is based on all arguments of the request
        hashed = hashlib.sha256(to_hash.encode('ascii', 'ignore')).hexdigest()

        if dbfile:
            # Check if there is a cached request for this hash
            cached = FeedDb(dbfile, 'cached_requests').retrieve(hashed)
            if cached:
                # Unpack and return the cached result instead of processing the request
                return pickle.loads(codecs.decode(cached.encode(), "base64"))
            else:
                #
                value = func(*args, **kwargs)
                FeedDb(dbfile, 'cached_requests').store(hashed, codecs.encode(pickle.dumps(value), "base64").decode())
                return value
        raise DbFileMissingExpection(str(args[0]))

    return cache_returned_values


@cache
def request(url, configfile, params=None, ajax=False, cloudproxy_session=False):
    config = CrawlerConfig('FeedCrawler', configfile)
    flaresolverr = config.get("flaresolverr")

    output = ''
    http_code = 500
    method = 'post' if (params is not None) else 'get'

    if ajax:
        headers = {'X-Requested-With': 'XMLHttpRequest'}
    else:
        headers = {}

    try:
        if flaresolverr:
            if not cloudproxy_session:
                json_session = requests.post(flaresolverr, headers=headers, data=dumps({
                    'cmd': 'sessions.create'
                }))
                response_session = loads(json_session.text)
                cloudproxy_session = response_session['session']

            headers['Content-Type'] = 'application/x-www-form-urlencoded' if (method == 'post') else 'application/json'

            json_response = requests.post(flaresolverr, headers=headers, data=dumps({
                'cmd': 'request.%s' % method,
                'url': url,
                'session': cloudproxy_session,
                'postData': '%s' % urlencode(params) if (method == 'post') else ''
            }))

            http_code = json_response.status_code
            response = loads(json_response.text)
            if 'solution' in response:
                output = response['solution']['response']

            if http_code == 500:
                requests.post(flaresolverr, headers=headers, data=dumps({
                    'cmd': 'sessions.destroy',
                    'session': cloudproxy_session,
                }))
                cloudproxy_session = None
        else:
            if method == 'post':
                response = requests.post(url, params, timeout=30, headers=headers)
            else:
                response = requests.get(url, timeout=30, headers=headers)

            output = response.text
            http_code = response.status_code
    except RequestException as e:
        print("Fehler im HTTP-Request", e)

    return {'http_code': http_code, 'output': output, 'cloudproxy_session': cloudproxy_session}
