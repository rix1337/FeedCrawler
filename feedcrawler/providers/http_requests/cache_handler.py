# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul sorgt durch Caching dafür, dass derselbe Request nur einmal pro Suchlauf an den Server geht.

import codecs
import hashlib
import pickle
from functools import wraps
from urllib.error import URLError

from feedcrawler.providers import shared_state
from feedcrawler.providers.common_functions import site_blocked, site_blocked_with_advanced_methods
from feedcrawler.providers.http_requests.cloudflare_handlers import flaresolverr_task
from feedcrawler.providers.http_requests.cloudflare_handlers import get_solver_url
from feedcrawler.providers.http_requests.cloudflare_handlers import sponsors_helper_task
from feedcrawler.providers.http_requests.request_handler import request
from feedcrawler.providers.sqlite_database import FeedDb


def cache(func):
    """Decorator that caches a functions return values for specific arguments."""

    @wraps(func)
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


@cache
def cached_request(url, method='get', params=None, headers=None, redirect_url=False, dont_cache=False):
    if dont_cache:
        shared_state.logger.debug("Aufruf ohne HTTP-Cache: " + url)

    sponsors_helper_url = get_solver_url("sponsors_helper")
    flaresolverr_url = get_solver_url("flaresolverr")

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

    status_code = 500
    text = ""
    response_headers = {}

    headers['User-Agent'] = shared_state.user_agent
    cookiejar = None
    proxies = {}
    force_ipv4 = False

    flaresolverr_run = False
    allow_sponsors_helper_run = False
    if sponsors_helper_url and not flaresolverr_url:
        allow_sponsors_helper_run = True

    while True:
        try:
            if site_blocked(url):
                if site_blocked_with_advanced_methods(url):
                    print("Die Seite %s ist blockiert..." % url)
                    return {'status_code': status_code, 'text': text, 'headers': response_headers, 'url': url}
                if allow_sponsors_helper_run:  # will only be used when flaresolverr is not available or not working
                    cookiejar, user_agent, proxy = sponsors_helper_task(sponsors_helper_url, url)
                    proxies = {"http": proxy, "https": proxy}
                    headers['User-Agent'] = user_agent
                    force_ipv4 = False
                    flaresolverr_run = False
                elif flaresolverr_url:
                    cookiejar, user_agent = flaresolverr_task(flaresolverr_url, url)
                    headers['User-Agent'] = user_agent
                    force_ipv4 = True
                    flaresolverr_run = True
                    allow_sponsors_helper_run = True

            if method == 'post':
                response = request(url, method="POST", data=params, timeout=10, headers=headers,
                                   cookiejar=cookiejar, proxies=proxies, force_ipv4=force_ipv4)
            else:
                response = request(url, timeout=10, headers=headers, cookiejar=cookiejar, proxies=proxies,
                                   force_ipv4=force_ipv4)

            if response.status_code == 403 or 'id="challenge-body-text"' in response.text:
                print("Die Cloudflare-Umgehung auf %s war nicht erfolgreich." % url)
                if flaresolverr_run and allow_sponsors_helper_run:
                    print("Lösung mit FlareSolverr gescheitert. Versuche es mit Sponsors Helper...")
                    continue  # try again with sponsors helper
                return {'status_code': status_code, 'text': text, 'headers': response_headers, 'url': url}

            if redirect_url:
                url = response.url
            status_code = response.status_code
            text = response.text
            response_headers = response.headers
        except URLError as e:
            print("Fehler im HTTP-Request", e)

        return {'status_code': status_code, 'text': text, 'headers': response_headers, 'url': url}
