# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul sorgt durch Caching dafür, dass derselbe Request nur einmal pro Suchlauf an den Server geht.

from functools import wraps
from urllib.error import URLError

from feedcrawler.providers import shared_state
from feedcrawler.providers.common_functions import check_is_site
from feedcrawler.providers.common_functions import site_blocked, site_blocked_with_advanced_methods
from feedcrawler.providers.http_requests.cloudflare_handlers import flaresolverr_task
from feedcrawler.providers.http_requests.cloudflare_handlers import get_solver_url
from feedcrawler.providers.http_requests.request_handler import request
from feedcrawler.providers.sqlite_database import FeedDb


def cache(func):
    """Decorator that caches a functions return values for specific arguments."""

    @wraps(func)
    def cache_returned_values(*args, **kwargs):
        if "dont_cache" in kwargs and kwargs["dont_cache"]:
            caching_allowed = False
        else:
            caching_allowed = True

        function_arguments_hash = str(hash(f"{args}{kwargs}"))

        try:
            cached_response = shared_state.values["request_" + function_arguments_hash]
        except KeyError:
            cached_response = None
        if cached_response:
            try:
                shared_state.update("request_cache_hits", shared_state.values["request_cache_hits"] + 1)
            except KeyError:
                shared_state.update("request_cache_hits", 1)
            return cached_response
        else:
            #
            value = func(*args, **kwargs)
            if caching_allowed:
                shared_state.update("request_" + function_arguments_hash, value)
            return value

    return cache_returned_values


@cache
def cached_request(url, method='get', params=None, headers=None, redirect_url=False, dont_cache=False):
    if dont_cache:
        shared_state.logger.debug("Aufruf ohne HTTP-Cache: " + url)

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

    headers['User-Agent'] = shared_state.values["user_agent"]
    cookiejar = None
    proxies = {}
    force_ipv4 = False

    while True:
        try:
            if site_blocked(url):
                if site_blocked_with_advanced_methods(url):
                    print(f"Der Aufruf von {url} wurde blockiert!")
                    return {'status_code': status_code, 'text': text, 'headers': response_headers, 'url': url}
                if flaresolverr_url:
                    cookiejar, user_agent = flaresolverr_task(flaresolverr_url, url)
                    headers['User-Agent'] = user_agent
                    force_ipv4 = True

            if method == 'post':
                response = request(url, method="POST", data=params, timeout=60, headers=headers,
                                   cookiejar=cookiejar, proxies=proxies, force_ipv4=force_ipv4)
            else:
                response = request(url, timeout=60, headers=headers, cookiejar=cookiejar, proxies=proxies,
                                   force_ipv4=force_ipv4)

            if response.status_code == 403 or 'id="challenge-body-text"' in response.text:
                print(f"Die Cloudflare-Umgehung auf {url} war nicht erfolgreich.")
                site = check_is_site(url)
                if site:
                    db_status = FeedDb('site_status')
                    normal_blocked = db_status.retrieve(site + "_normal")
                    if not normal_blocked:
                        db_status.store(site + "_normal", "Blocked")
                        if flaresolverr_url:
                            print("Versuche es mit Cloudfare-Umgehung erneut...")
                            continue  # try again with any solver
                    else:
                        advanced_blocked = db_status.retrieve(site + "_advanced")
                        if not advanced_blocked:
                            db_status.store(site + "_advanced", "Blocked")
                return {'status_code': status_code, 'text': text, 'headers': response_headers, 'url': url}

            if redirect_url:
                url = response.url
            status_code = response.status_code
            text = response.text
            response_headers = response.headers
        except URLError as e:
            print("Fehler im HTTP-Request", e)

        return {'status_code': status_code, 'text': text, 'headers': response_headers, 'url': url}
