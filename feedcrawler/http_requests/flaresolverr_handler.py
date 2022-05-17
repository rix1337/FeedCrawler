# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul integriert den FlareSolverr, um Cloudflare-Blockaden zu umgehen.

from json import loads
from urllib.parse import urlencode

from feedcrawler import internal
from feedcrawler.common import site_blocked_with_flaresolverr
from feedcrawler.config import CrawlerConfig
from feedcrawler.db import ListDb
from feedcrawler.http_requests.request_handler import request


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
            request(flaresolverr_url, headers={}, method="POST", json={
                'cmd': 'sessions.destroy',
                'session': flaresolverr_session
            })
        ListDb('flaresolverr_sessions').reset()


def flaresolverr_request(flaresolverr_url, url, method, params, headers, redirect_url):
    flaresolverr_session = get_flaresolverr_session()
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

    internal.logger.debug("Versuche Cloudflare auf der Seite %s mit dem FlareSolverr zu umgehen..." % url)
    if not flaresolverr_session:
        json_session = request(flaresolverr_url, method="POST", json={
            'cmd': 'sessions.create'
        })
        response_session = loads(json_session.text)
        flaresolverr_session = response_session['session']
    elif site_blocked_with_flaresolverr(url) and flaresolverr_proxy:
        internal.logger.debug("Proxy ist notwendig. Zerstöre aktive Sessions",
                              flaresolverr_session)
        clean_flaresolverr_sessions()
        json_session = request(flaresolverr_url, method="POST", json={
            'cmd': 'sessions.create'
        })
        response_session = loads(json_session.text)
        flaresolverr_session = response_session['session']

    headers['Content-Type'] = 'application/x-www-form-urlencoded' if (
            method == 'post') else 'application/json'

    flaresolverr_payload = {
        'cmd': 'request.%s' % method,
        'url': url,
        'session': flaresolverr_session
    }

    if method == 'post':
        flaresolverr_payload["postData"] = encoded_params

    if site_blocked_with_flaresolverr(url) and flaresolverr_proxy:
        flaresolverr_payload["proxy"] = {"url": flaresolverr_proxy}

    json_response = request(flaresolverr_url, method="POST", json=flaresolverr_payload)

    status_code = json_response.status_code

    if status_code == 500:
        internal.logger.debug("Der Request für " + url + " ist fehlgeschlagen. Zerstöre die Session" +
                              str(flaresolverr_session))
        clean_flaresolverr_sessions()
        flaresolverr_session = None

    response = loads(json_response.text)
    if 'solution' in response:
        if redirect_url:
            try:
                url = response['solution']['url']
            except:
                internal.logger.debug("Der Abruf der Redirect-URL war mit FlareSolverr fehlerhaft.")
        text = response['solution']['response']
        response_headers = response['solution']['headers']

    if flaresolverr_session:
        save_flaresolverr_session(flaresolverr_session)

    return status_code, text, response_headers, url
