# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul sorgt durch Caching dafür, dass der selbe Request nur einmal pro Suchlauf an den Server geht.
# Dieses Modul integriert weiterhin, wo immer notwendig, den FlareSolverr, um Cloudflare-Blockaden zu umgehen.

import codecs
import functools
import hashlib
import pickle
from json import loads
from urllib.parse import urlencode

import requests
from requests import RequestException

from feedcrawler import internal
from feedcrawler.common import site_blocked
from feedcrawler.common import site_blocked_with_flaresolverr
from feedcrawler.config import CrawlerConfig
from feedcrawler.db import FeedDb
from feedcrawler.db import ListDb


def cache(func):
    """Decorator that caches a functions return values for specific arguments."""

    @functools.wraps(func)
    def cache_returned_values(*args, **kwargs):
        to_hash = ""
        dont_cache = False
        for a in args:
            to_hash += codecs.encode(pickle.dumps(a), "base64").decode()
        for k in kwargs:
            to_hash += codecs.encode(pickle.dumps(k), "base64").decode()
            to_hash += codecs.encode(pickle.dumps(kwargs[k]), "base64").decode()
            if k == "dont_cache" and k:
                dont_cache = True
        # This hash is based on all arguments of the request
        hashed = hashlib.sha256(to_hash.encode('ascii', 'ignore')).hexdigest()

        cached = FeedDb('cached_requests').retrieve(hashed)
        if cached:
            # Unpack and return the cached result instead of processing the request
            return pickle.loads(codecs.decode(cached.encode(), "base64"))
        else:
            #
            value = func(*args, **kwargs)
            if not dont_cache:
                FeedDb('cached_requests').store(hashed, codecs.encode(pickle.dumps(value), "base64").decode())
            return value

    return cache_returned_values


def get_flaresolverr_url():
    config = CrawlerConfig('FeedCrawler')
    flaresolverr = config.get("flaresolverr")
    if flaresolverr:
        return flaresolverr + "/v1"
    return False


def get_flaresolverr_proxy():
    config = CrawlerConfig('FeedCrawler')
    flaresolverr_proxy = config.get("flaresolverr_proxy")
    if flaresolverr_proxy:
        return flaresolverr_proxy
    return False


def get_flaresolverr_session():
    flaresolverr_sessions = ListDb('flaresolverr_sessions').retrieve()
    try:
        return flaresolverr_sessions[0]
    except:
        return False


def save_flaresolverr_session(flaresolverr_session):
    flaresolverr_sessions = ListDb('flaresolverr_sessions').retrieve()
    if (flaresolverr_sessions and flaresolverr_session not in flaresolverr_sessions) or not flaresolverr_sessions:
        ListDb('flaresolverr_sessions').store(flaresolverr_session)


def clean_flaresolverr_sessions():
    flaresolverr_url = get_flaresolverr_url()
    flaresolverr_sessions = ListDb('flaresolverr_sessions').retrieve()
    if flaresolverr_sessions:
        for flaresolverr_session in flaresolverr_sessions:
            requests.post(flaresolverr_url, headers={}, json={
                'cmd': 'sessions.destroy',
                'session': flaresolverr_session
            })
        ListDb('flaresolverr_sessions').reset()


@cache
def request(url, method='get', params=None, headers=None, redirect_url=False, dont_cache=False):
    if dont_cache:
        internal.logger.debug("Disabled request caching for request of: " + url)

    flaresolverr_url = get_flaresolverr_url()
    flaresolverr_session = get_flaresolverr_session()
    flaresolverr_proxy = get_flaresolverr_proxy()

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
        if site_blocked(url):
            if flaresolverr_url:
                internal.logger.debug("Versuche Cloudflare auf der Seite %s mit dem FlareSolverr zu umgehen..." % url)
                if not flaresolverr_session:
                    json_session = requests.post(flaresolverr_url, json={
                        'cmd': 'sessions.create'
                    })
                    response_session = loads(json_session.text)
                    flaresolverr_session = response_session['session']
                elif site_blocked_with_flaresolverr(url) and flaresolverr_proxy:
                    internal.logger.debug("Proxy ist notwendig. Zerstöre aktive Sessions",
                                          flaresolverr_session)
                    clean_flaresolverr_sessions()
                    json_session = requests.post(flaresolverr_url, json={
                        'cmd': 'sessions.create'
                    })
                    response_session = loads(json_session.text)
                    flaresolverr_session = response_session['session']

                headers['Content-Type'] = 'application/x-www-form-urlencoded' if (
                        method == 'post') else 'application/json'

                flaresolverr_payload = {
                    'cmd': 'request.%s' % method,
                    'url': url,
                    'session': flaresolverr_session,
                    # Not available in FlareSolverr v.2.X.X 'headers': headers
                }

                if method == 'post':
                    flaresolverr_payload["postData"] = encoded_params

                if site_blocked_with_flaresolverr(url) and flaresolverr_proxy:
                    flaresolverr_payload["proxy"] = {"url": flaresolverr_proxy}

                json_response = requests.post(flaresolverr_url, json=flaresolverr_payload)

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
                    internal.logger.debug("Der Request für " + url + " ist fehlgeschlagen. Zerstöre die Session" +
                                          str(flaresolverr_session))
                    clean_flaresolverr_sessions()
                    flaresolverr_session = None
            else:
                internal.logger.debug(
                    "Um Cloudflare auf der Seite %s zu umgehen, muss ein FlareSolverr konfiguriert werden." % url)
                return {'status_code': status_code, 'text': "", 'headers': {}}
        else:
            if method == 'post':
                response = requests.post(url, data=params, timeout=10, headers=headers)
            elif redirect_url:
                try:
                    return requests.get(url, allow_redirects=False, timeout=10).headers._store["location"][1]
                except:
                    internal.logger.debug("Der Abruf der Redirect-URL war ohne FlareSolverr fehlerhaft.")
                    return url
            else:
                response = requests.get(url, timeout=10, headers=headers)

            status_code = response.status_code
            text = response.text
            response_headers = response.headers
    except RequestException as e:
        print("Fehler im HTTP-Request", e)

    if flaresolverr_session:
        save_flaresolverr_session(flaresolverr_session)

    return {'status_code': status_code, 'text': text, 'headers': response_headers}
