# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul integriert den FlareSolverr, um Cloudflare-Blockaden zu umgehen.

from json import loads
from urllib.parse import urlencode

from feedcrawler.providers import shared_state
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.http_requests.request_handler import request


def get_flaresolverr_url():
    config = CrawlerConfig('FeedCrawler')
    flaresolverr = config.get("flaresolverr")
    if flaresolverr:
        if flaresolverr.endswith('/'):
            flaresolverr = flaresolverr[:-1]
            config.save('flaresolverr', flaresolverr)
        return flaresolverr + "/v1"
    return False


def flaresolverr_request(flaresolverr_url, url, method, params, headers, redirect_url):
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

    return status_code, text, response_headers, url
