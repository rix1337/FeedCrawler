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
from feedcrawler.providers.common_functions import site_blocked
from feedcrawler.providers.http_requests.flaresolverr_handler import flaresolverr_request
from feedcrawler.providers.http_requests.flaresolverr_handler import get_flaresolverr_url
from feedcrawler.providers.http_requests.request_handler import request
from feedcrawler.providers.http_requests.sponsors_helper_handler import get_sponsors_helper_url
from feedcrawler.providers.http_requests.sponsors_helper_handler import sponsors_helper_cookies_and_user_agent
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

    sponsors_helper_url = get_sponsors_helper_url()
    flaresolverr_url = get_flaresolverr_url()

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

    text = ''
    status_code = 500
    response_headers = {}

    try:
        if site_blocked(url):
            if sponsors_helper_url:
                cookiejar, user_agent, proxy = sponsors_helper_cookies_and_user_agent(sponsors_helper_url, url)

                proxies = {"http": proxy, "https": proxy}

                headers['User-Agent'] = user_agent
                if method == 'post':
                    response = request(url, method="POST", data=params, timeout=10, headers=headers,
                                       cookiejar=cookiejar, proxies=proxies)
                elif redirect_url:
                    try:
                        response = request(url, timeout=10, cookiejar=cookiejar, proxies=proxies)
                        if response.status_code == 403 or 'id="challenge-body-text"' in response.text:
                            shared_state.logger.debug(
                                "Sponsors Helper konnte die Cloudflare-Blockade auf %s nicht umgehen." % url)
                        else:
                            return {'status_code': status_code, 'text': "", 'headers': {}}

                        return response.url
                    except Exception as e:
                        pass
                    shared_state.logger.debug(
                        "Der Abruf der Redirect-URL war mit Sponsors Helper fehlerhaft: " + str(e))
                    return url
                else:
                    response = request(url, timeout=10, headers=headers, cookiejar=cookiejar, proxies=proxies)

                if response.status_code == 403 or 'id="challenge-body-text"' in response.text:
                    shared_state.logger.debug(
                        "Sponsors Helper konnte die Cloudflare-Blockade auf %s nicht umgehen." % url)
                    return {'status_code': status_code, 'text': "", 'headers': {}}

                status_code = response.status_code
                text = response.text
                response_headers = response.headers
            elif flaresolverr_url:
                status_code, text, response_headers, url = flaresolverr_request(flaresolverr_url, url, method, params,
                                                                                headers, redirect_url)
                if redirect_url:
                    shared_state.logger.debug(
                        "FlaresSolverr ist nicht in der Lage, die Redirect-URL von %s abzurufen." % url)
                    return url
            else:
                shared_state.logger.debug(
                    "Um Cloudflare auf der Seite %s zu umgehen, müssen Sponsors Helper oder FlareSolverr konfiguriert werden." % url)
                return {'status_code': status_code, 'text': "", 'headers': {}}
        else:
            headers['User-Agent'] = shared_state.user_agent
            if method == 'post':
                response = request(url, method="POST", data=params, timeout=10, headers=headers)
            elif redirect_url:
                try:
                    return request(url, timeout=10).url
                except Exception as e:
                    shared_state.logger.debug("Der Abruf der Redirect-URL war fehlerhaft: " + str(e))
                    return url
            else:
                response = request(url, timeout=10, headers=headers)

            status_code = response.status_code
            text = response.text
            response_headers = response.headers
    except URLError as e:
        print("Fehler im HTTP-Request", e)

    return {'status_code': status_code, 'text': text, 'headers': response_headers}
