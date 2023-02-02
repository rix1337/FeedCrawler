# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul integriert den FlareSolverr, um Cloudflare-Blockaden zu umgehen.

import codecs
import http.cookiejar
import pickle
from json import loads
from urllib.error import URLError
from urllib.parse import urlencode

from feedcrawler.providers import shared_state
from feedcrawler.providers.common_functions import site_blocked_with_flaresolverr
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.http_requests.request_handler import request
from feedcrawler.providers.sqlite_database import FeedDb


def get_flaresolverr_url():
    config = CrawlerConfig('FeedCrawler')
    flaresolverr = config.get("flaresolverr")
    if flaresolverr:
        if flaresolverr.endswith('/'):
            flaresolverr = flaresolverr[:-1]
            config.save('flaresolverr', flaresolverr)
        return flaresolverr + "/v1"
    return False


def get_flaresolverr_proxy():
    config = CrawlerConfig('FeedCrawler')
    flaresolverr_proxy = config.get("flaresolverr_proxy")
    if flaresolverr_proxy:
        return flaresolverr_proxy
    return False


def pickle_db(key, value):
    try:
        FeedDb('flaresolverr').delete(key)
        return FeedDb('flaresolverr').store(key, codecs.encode(pickle.dumps(value), "base64").decode())
    except:
        pass
    return False


def unpickle_db(key):
    try:
        pickled = FeedDb('flaresolverr').retrieve(key)
        if pickled:
            return pickle.loads(codecs.decode(pickled.encode(), "base64"))
    except:
        pass
    return False


def clean_flaresolverr_session():
    # ToDo: as soon as FlareSolverr 3.0 supports sessions we need to send a delete request to the session endpoint
    return FeedDb('flaresolverr').reset()


def set_flaresolverr_session(cookies, headers, user_agent):
    try:
        cookiejar = pickle_db('cookies', cookies)
        headers = pickle_db('headers', headers)
        user_agent = pickle_db('user_agent', user_agent)
        if cookiejar and headers and user_agent:
            return True
    except:
        pass
    return False


def get_flaresolverr_session():
    cookies = unpickle_db('cookies')
    headers = unpickle_db('headers')
    user_agent = unpickle_db('user_agent')
    cookiejar = http.cookiejar.CookieJar()

    if cookies:
        for cookie in cookies:
            if cookie['name'] == 'cf_clearance' and cookie['value']:
                cookie = http.cookiejar.Cookie(
                    version=0,
                    name=cookie['name'],
                    value=cookie['value'],
                    port=None,
                    port_specified=False,
                    domain=cookie['domain'],
                    domain_specified=bool(cookie['domain']),
                    domain_initial_dot=bool(cookie['domain'].startswith('.')),
                    path=cookie['path'],
                    path_specified=True,
                    secure=True,
                    expires=cookie['expiry'],
                    discard=True,
                    comment=None,
                    comment_url=None,
                    rest={
                        'HttpOnly': bool(cookie['httpOnly']),
                        'sameSite': 'None'
                    },
                    rfc2109=False,
                )
                cookiejar.set_cookie(cookie)
                break

        return cookiejar, headers, user_agent
    return False, False, False


def flaresolverr_request(flaresolverr_url, url, method, params, headers, redirect_url):
    session_cookiejar, session_headers, session_user_agent = get_flaresolverr_session()
    # ToDo: as soon as FlareSolverr 3.0 supports headers, this should be true and hopefully working
    if session_cookiejar and session_headers and session_user_agent:
        shared_state.logger.debug(
            "Cloudflare-Session gefunden. Versuche Seite %s ohne Flaresolverr aufzurufen..." % url)

        session_headers['User-Agent'] = session_user_agent

        try:
            result = request(url, method=method, data=params, timeout=10,
                             headers=session_headers,
                             cookiejar=session_cookiejar
                             )

            if result.status_code == 200:
                shared_state.logger.debug("Cloudflare-Cookie erfolgreich verwendet.")
                return result.status_code, result.text, result.headers, result.url
            else:
                shared_state.logger.debug("Cloudflare-Session ungültig!")
                clean_flaresolverr_session()

        except URLError as e:
            shared_state.logger.debug("Cloudflare-Session ungültig!.")
            clean_flaresolverr_session()
            print("Fehler im HTTP-Request (ohne Flaresolverr)", e)

    flaresolverr_proxy = get_flaresolverr_proxy()

    text = ''
    response_headers = {}

    if params:
        try:
            encoded_params = urlencode(params)
        except:
            encoded_params = params
    else:
        encoded_params = params

    shared_state.logger.debug("Versuche Cloudflare auf der Seite %s mit dem FlareSolverr zu umgehen..." % url)

    headers['Content-Type'] = 'application/x-www-form-urlencoded' if (
            method == 'post') else 'application/json'

    flaresolverr_payload = {
        'cmd': 'request.%s' % method,
        'url': url
    }

    if method == 'post':
        flaresolverr_payload["postData"] = encoded_params

    if site_blocked_with_flaresolverr(url) and flaresolverr_proxy:
        flaresolverr_payload["proxy"] = {"url": flaresolverr_proxy}

    json_response = request(flaresolverr_url, method="POST", json=flaresolverr_payload)

    status_code = json_response.status_code

    if status_code == 500:
        shared_state.logger.debug("Der Request für " + url + " ist fehlgeschlagen.")

    response = loads(json_response.text)

    if 'solution' in response:
        if redirect_url:
            try:
                url = response['solution']['url']
                shared_state.logger.debug("Der Abruf der Redirect-URL war mit FlareSolverr erfolgreich.")
            except:
                shared_state.logger.debug("Der Abruf der Redirect-URL war mit FlareSolverr fehlerhaft.")

        shared_state.logger.debug("Der Abruf der URL war mit FlareSolverr erfolgreich.")

        text = response['solution']['response']
        response_headers = response['solution']['headers']
        new_session_cookies = response['solution']['cookies']
        new_session_headers = response['solution']['headers']
        new_session_user_agent = response['solution']['userAgent']

        set_flaresolverr_session(new_session_cookies, new_session_headers, new_session_user_agent)

    return status_code, text, response_headers, url
