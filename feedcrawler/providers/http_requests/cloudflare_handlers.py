# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul integriert Tools, die valide Cookies+User Agents bereitstellen, um Cloudflare-Blockaden zu umgehen.

import codecs
import http.cookiejar
import pickle
import time
from json import loads

from feedcrawler.providers import shared_state
from feedcrawler.providers.common_functions import check_is_site
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.http_requests.request_handler import request
from feedcrawler.providers.sqlite_database import FeedDb


def clean_db(db, key):
    FeedDb(db).delete(key)


def pickle_db(db, key, value):
    try:
        clean_db(db, key)
        return FeedDb(db).store(key, codecs.encode(pickle.dumps(value), "base64").decode())
    except:
        pass
    return False


def unpickle_db(db, key):
    try:
        pickled = FeedDb(db).retrieve(key)
        if pickled:
            return pickle.loads(codecs.decode(pickled.encode(), "base64"))
    except:
        pass
    return {}


def cookie_dict_to_cookiejar(cookies):
    cf_clearance = False
    cookiejar = http.cookiejar.CookieJar()
    names_from_jar = [cookie.name for cookie in cookiejar]
    for name in cookies:
        if name == "cf_clearance" and name not in names_from_jar:
            cookiejar.set_cookie(create_cookie(name, cookies[name]))
            cf_clearance = True
    if not cf_clearance:
        shared_state.logger.debug("No cf_clearance cookie found in solution.")
    return cookiejar


def create_cookie(name, value, **kwargs):
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


def get_solver_url(solver_internal_name):
    config = CrawlerConfig('FeedCrawler')
    solver_url = config.get(solver_internal_name)
    if solver_url:
        if solver_url.endswith('/'):
            solver_url = solver_url[:-1]
            config.save(solver_internal_name, solver_url)
        return solver_url
    return False


def test_solver_url(solver_internal_name, solver_status_endpoint):
    if solver_internal_name == "sponsors_helper":
        solver_log_name = "Sponsors Helper"
    elif solver_internal_name == "flaresolverr":
        solver_log_name = "FlareSolverr"
    else:
        print("Ungültiger Solver: " + solver_internal_name)
        return False

    try:
        if request(solver_status_endpoint, timeout=30).status_code == 200:
            return True
    except:
        pass
    try:
        time.sleep(30)  # during updates and boot the service might not be ready yet
        if request(solver_status_endpoint, timeout=30).status_code == 200:
            return True
    except:
        pass
    print(solver_log_name + " nicht erreichbar. Bitte die Konfiguration überprüfen!")
    return False


def get_local_proxy_url(solver_url, proxy_url):
    try:
        solver_scheme = solver_url.split(":")[0]
        solver_adress = solver_url.split(":")[1].replace("//", "")

        proxy_user = proxy_url.split(":")[1].replace("//", "")
        proxy_pass = proxy_url.split(":")[2].split("@")[0]
        proxy_port = proxy_url.split(":")[3].replace("/", "")

        local_proxy_url = solver_scheme + "://" + proxy_user + ":" + proxy_pass + "@" + solver_adress + ":" + proxy_port

        return local_proxy_url
    except:
        pass
    return proxy_url


def test_challenge_path(url):
    site = check_is_site(url)
    if site and site == "HW":
        return "/category/neuerscheinung/"
    else:
        return "/"


def sponsors_helper_task(solver_url, url):
    base_domain = url.split("/")[2]
    last_solution = unpickle_db("sponsors_helper", base_domain)
    if last_solution:
        try:
            if last_solution["valid_until"] > int(time.time()):
                cookiejar = cookie_dict_to_cookiejar(last_solution["cookies"])
                user_agent = last_solution["user_agent"]
                proxy = get_local_proxy_url(solver_url, last_solution["proxy"])
                if cookiejar:
                    shared_state.logger.debug("Bestehende Cloudflare-Cookies werden für " + url + " verwendet.")
                    return cookiejar, user_agent, proxy
            else:
                clean_db("sponsors_helper", base_domain)
        except:
            pass

    if test_solver_url("sponsors_helper", solver_url + "/status"):
        shared_state.logger.debug(
            "Versuche Cloudflare auf der Seite %s mit Sponsors Helper zu umgehen..." % url)

        solver_endpoint = "/cloudflare_cookie/"
        solver_payload = {
            'url': "https://" + base_domain + test_challenge_path(url)
        }

        response = request(
            solver_url + solver_endpoint,
            method="POST",
            json=solver_payload,
            timeout=180)

        if response.status_code == 200:
            try:
                response = loads(response.text)
                cookies = response["cookies"]
                if cookies:
                    cookiejar = cookie_dict_to_cookiejar(cookies)
                    user_agent = response["user_agent"]
                    proxy = get_local_proxy_url(solver_url, response["proxy"])
                    valid_until = int(time.time()) + 1800 - 60

                    pickle_db("sponsors_helper",
                              base_domain,
                              {
                                  "cookies": cookies,
                                  "user_agent": user_agent,
                                  "proxy": proxy,
                                  "valid_until": valid_until
                              })

                    shared_state.logger.debug(
                        "Die Erzeugung von Cloudflare-Cookies für " + url + " war mit Sponsors Helper erfolgreich.")
                    return cookiejar, user_agent, proxy
            except:
                pass
        else:
            shared_state.logger.debug(
                "Die Erzeugung von Cloudflare-Cookies für " + url + " ist mit Sponsors Helper fehlgeschlagen.")
    return False, False


def flaresolverr_task(solver_url, url):
    base_domain = url.split("/")[2]
    last_solution = unpickle_db("flaresolverr", base_domain)
    if last_solution:
        try:
            if last_solution["valid_until"] > int(time.time()):
                cookiejar = cookie_dict_to_cookiejar(last_solution["cookies"])
                user_agent = last_solution["user_agent"]
                if cookiejar:
                    shared_state.logger.debug(
                        "Bestehende Cloudflare-Cookies werden für " + url + " verwendet.")
                    return cookiejar, user_agent
            else:
                clean_db("flaresolverr", base_domain)
        except:
            pass

    if test_solver_url("flaresolverr", solver_url):
        shared_state.logger.debug(
            "Versuche Cloudflare auf der Seite %s mit  FlareSolverr zu umgehen..." % url)

        solver_endpoint = "/v1"
        solver_payload = {
            'cmd': 'request.get',
            'url': "https://" + base_domain + test_challenge_path(url)
        }

        response = request(
            solver_url + solver_endpoint,
            method="POST",
            json=solver_payload,
            timeout=60)

        if response.status_code == 200:
            try:
                response = loads(response.text)
                domain_cookies = response["solution"]["cookies"]
                cookies = {}
                for cookie in domain_cookies:
                    if base_domain in cookie["domain"]:
                        cookies[cookie["name"]] = cookie["value"]

                if cookies:
                    cookiejar = cookie_dict_to_cookiejar(cookies)
                    user_agent = response["solution"]["userAgent"]
                    valid_until = int(time.time()) + 1800 - 60

                    pickle_db("flaresolverr",
                              base_domain,
                              {
                                  "cookies": cookies,
                                  "user_agent": user_agent,
                                  "valid_until": valid_until
                              })

                    shared_state.logger.debug(
                        "Die Erzeugung von Cloudflare-Cookies für " + url + " war mit FlareSolverr erfolgreich.")
                    return cookiejar, user_agent
            except:
                pass
        else:
            shared_state.logger.debug(
                "Die Erzeugung von Cloudflare-Cookies für " + url + " ist mit FlareSolverr fehlgeschlagen.")
    return False, False
