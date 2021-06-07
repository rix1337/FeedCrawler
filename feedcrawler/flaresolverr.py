# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337

import codecs
import functools
import hashlib
import pickle
from json import dumps, loads
from urllib.parse import urlencode

import requests
from requests import RequestException

from feedcrawler import internal
from feedcrawler.common import check_site_blocked
from feedcrawler.config import CrawlerConfig
from feedcrawler.db import FeedDb
from feedcrawler.db import ListDb


def cache(func):
    """Decorator that caches a functions return values for specific arguments."""

    @functools.wraps(func)
    def cache_returned_values(*args, **kwargs):
        to_hash = ""
        for a in args:
            to_hash += codecs.encode(pickle.dumps(a), "base64").decode()
        for k in kwargs:
            to_hash += codecs.encode(pickle.dumps(k), "base64").decode()
            to_hash += codecs.encode(pickle.dumps(kwargs[k]), "base64").decode()
        # This hash is based on all arguments of the request
        hashed = hashlib.sha256(to_hash.encode('ascii', 'ignore')).hexdigest()

        cached = FeedDb('cached_requests').retrieve(hashed)
        if cached:
            # Unpack and return the cached result instead of processing the request
            return pickle.loads(codecs.decode(cached.encode(), "base64"))
        else:
            #
            value = func(*args, **kwargs)
            FeedDb('cached_requests').store(hashed, codecs.encode(pickle.dumps(value), "base64").decode())
            return value

    return cache_returned_values


def get_flaresolverr_url():
    config = CrawlerConfig('FeedCrawler')
    flaresolverr = config.get("flaresolverr")
    if flaresolverr:
        return flaresolverr + "/v1"
    return False


def get_cloudproxy_session():
    cloudproxy_sessions = ListDb('flaresolverr_sessions').retrieve()
    try:
        return cloudproxy_sessions[0]
    except:
        return False


def save_cloudproxy_session(cloudproxy_session):
    cloudproxy_sessions = ListDb('flaresolverr_sessions').retrieve()
    if (cloudproxy_sessions and cloudproxy_session not in cloudproxy_sessions) or not cloudproxy_sessions:
        ListDb('flaresolverr_sessions').store(cloudproxy_session)


def clean_cloudproxy_sessions():
    flaresolverr_url = get_flaresolverr_url()
    cloudproxy_sessions = ListDb('flaresolverr_sessions').retrieve()
    if cloudproxy_sessions:
        for cloudproxy_session in cloudproxy_sessions:
            requests.post(flaresolverr_url, headers={}, data=dumps({
                'cmd': 'sessions.destroy',
                'session': cloudproxy_session
            }))
        ListDb('flaresolverr_sessions').reset()


@cache
def request(url, method='get', params=None, headers=None, redirect_url=False):
    flaresolverr_url = get_flaresolverr_url()
    cloudproxy_session = get_cloudproxy_session()

    if not headers:
        headers = {}
    else:
        try:
            if headers['If-Modified-Since'] == 'None':
                del headers['If-Modified-Since']
        except:
            pass
    if "ajax" in url.lower():
        headers['X-Requested-With'] = 'XMLHttpRequest'

    if params:
        try:
            encoded_params = urlencode(params)
        except:
            encoded_params = params
    else:
        encoded_params = params

    text = ''
    status_code = 500
    response_headers = {}

    try:
        if check_site_blocked(url):
            if flaresolverr_url:
                internal.logger.debug("Versuche Cloudflare auf der Seite %s mit dem FlareSolverr zu umgehen..." % url)
                if not cloudproxy_session:
                    json_session = requests.post(flaresolverr_url, data=dumps({
                        'cmd': 'sessions.create'
                    }))
                    response_session = loads(json_session.text)
                    cloudproxy_session = response_session['session']

                headers['Content-Type'] = 'application/x-www-form-urlencoded' if (
                        method == 'post') else 'application/json'

                json_response = requests.post(flaresolverr_url, data=dumps({
                    'cmd': 'request.%s' % method,
                    'url': url,
                    'session': cloudproxy_session,
                    'headers': headers,
                    'postData': '%s' % encoded_params if (method == 'post') else ''
                }))

                status_code = json_response.status_code
                response = loads(json_response.text)

                if 'solution' in response:
                    if redirect_url:
                        try:
                            return response['solution']['url']
                        except:
                            internal.logger.debug("Der Abruf der Redirect-URL war mit FlareSolverr fehlerhaft.")
                            return url
                    text = response['solution']['response']
                    response_headers = response['solution']['headers']

                if status_code == 500:
                    internal.logger.debug("Der Request für", url, "ist fehlgeschlagen. Zerstöre die Session",
                                          cloudproxy_session)
                    requests.post(flaresolverr_url, data=dumps({
                        'cmd': 'sessions.destroy',
                        'session': cloudproxy_session,
                    }))
                    cloudproxy_session = None
            else:
                internal.logger.debug(
                    "Um Cloudflare auf der Seite %s zu umgehen, muss ein FlareSolverr konfiguriert werden." % url)
                return ""
        else:
            if method == 'post':
                response = requests.post(url, data=params, timeout=30, headers=headers)
            elif redirect_url:
                try:
                    return requests.get(url, allow_redirects=False).headers._store["location"][1]
                except:
                    internal.logger.debug("Der Abruf der Redirect-URL war ohne FlareSolverr fehlerhaft.")
                    return url
            else:
                response = requests.get(url, timeout=30, headers=headers)

            status_code = response.status_code
            text = response.text
            response_headers = response.headers
    except RequestException as e:
        print("Fehler im HTTP-Request", e)

    if cloudproxy_session:
        save_cloudproxy_session(cloudproxy_session)

    return {'status_code': status_code, 'text': text, 'headers': response_headers}
