# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul integriert den Sponsors Helper, um Cloudflare-Blockaden zu umgehen.


import codecs
import http.cookiejar
import pickle
import time
from json import loads

from feedcrawler.providers import shared_state
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.http_requests.request_handler import request
from feedcrawler.providers.sqlite_database import FeedDb


def get_sponsors_helper_url():
    config = CrawlerConfig('FeedCrawler')
    sponsors_helper = config.get("sponsors_helper")
    if sponsors_helper:
        if sponsors_helper.endswith('/'):
            sponsors_helper = sponsors_helper[:-1]
            config.save('sponsors_helper', sponsors_helper)
        try:
            if request(sponsors_helper + "/status").status_code == 200:
                return sponsors_helper + "/cloudflare_cookie/"
        except:
            pass
    return False


def pickle_db(key, value):
    try:
        clean_db(key)
        return FeedDb('sponsors_helper').store(key, codecs.encode(pickle.dumps(value), "base64").decode())
    except:
        pass
    return False


def unpickle_db(key):
    try:
        pickled = FeedDb('sponsors_helper').retrieve(key)
        if pickled:
            return pickle.loads(codecs.decode(pickled.encode(), "base64"))
    except:
        pass
    return {}


def clean_db(key):
    FeedDb('sponsors_helper').delete(key)


def cookie_dict_to_cookiejar(cookies):
    cookiejar = http.cookiejar.CookieJar()
    names_from_jar = [cookie.name for cookie in cookiejar]
    for name in cookies:
        if name == "cf_clearance" and name not in names_from_jar:
            cookiejar.set_cookie(create_cookie(name, cookies[name]))
    return cookiejar


def create_cookie(name, value, **kwargs):
    """Make a cookie from underspecified parameters.

    By default, the pair of `name` and `value` will be set for the domain ''
    and sent on every request (this is sometimes called a "supercookie").
    """
    result = dict(
        version=0,
        name=name,
        value=value,
        port=None,
        domain='',
        path='/',
        secure=True,
        expires=None,
        discard=True,
        comment=None,
        comment_url=None,
        rest={'HttpOnly': None},
        rfc2109=False, )

    badargs = set(kwargs) - set(result)
    if badargs:
        err = 'create_cookie() got unexpected keyword arguments: %s'
        raise TypeError(err % list(badargs))

    result.update(kwargs)
    result['port_specified'] = bool(result['port'])
    result['domain_specified'] = bool(result['domain'])
    result['domain_initial_dot'] = result['domain'].startswith('.')
    result['path_specified'] = bool(result['path'])

    return http.cookiejar.Cookie(**result)


def sponsors_helper_cookies_and_user_agent(sponsors_helper_url, url):
    shared_state.logger.debug("Versuche Cloudflare auf der Seite %s mit dem Sponsors Helper zu umgehen..." % url)

    base_domain = url.split("/")[2]
    last_solution = unpickle_db(base_domain)
    if last_solution:
        try:
            if last_solution["valid_until"] > int(time.time()):
                cookiejar = cookie_dict_to_cookiejar(last_solution["cookies"])
                user_agent = last_solution["user_agent"]
                proxy = last_solution["proxy"]
                if cookiejar:
                    shared_state.logger.debug("Die Erzeugung von Cloudflare-Cookies für " + url + " war erfolgreich.")
                    return cookiejar, user_agent, proxy
            else:
                clean_db(base_domain)
        except:
            pass

    sponsors_helper_payload = {
        'url': url
    }

    json_response = request(sponsors_helper_url, method="POST", json=sponsors_helper_payload)

    status_code = json_response.status_code

    if not status_code == 200:
        shared_state.logger.debug("Die Erzeugung von Cloudflare-Cookies für " + url + " ist fehlgeschlagen.")

    response = loads(json_response.text)

    try:
        cookies = response["cookies"]
        if cookies:
            cookiejar = cookie_dict_to_cookiejar(cookies)
            user_agent = response["user_agent"]
            proxy = response["proxy"]
            valid_until = int(time.time()) + 1800 - 60

            shared_state.logger.debug("Die Erzeugung von Cloudflare-Cookies für " + url + " war erfolgreich.")
            pickle_db(base_domain,
                      {"cookies": cookies, "user_agent": user_agent, "proxy": proxy, "valid_until": valid_until})

            return cookiejar, user_agent, proxy

    except:
        pass

    return False, False
