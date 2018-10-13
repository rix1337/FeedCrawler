# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337
# Enthält Code von:
# https://github.com/Gutz-Pilz/pyLoad-stuff/blob/master/SJ.py

import logging
import re

import six
from six.moves.urllib.error import HTTPError
from six.moves.urllib.parse import urlencode
from six.moves.urllib.request import urlopen, Request

from rsscrawler.rssconfig import RssConfig

try:
    import simplejson as json
except ImportError:
    import json

log_info = logging.info
log_error = logging.error
log_debug = logging.debug


def api_request_cutter(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def notify(added_items, configfile):
    notifications = RssConfig('Notifications', configfile)
    homeassistant_settings = notifications.get("homeassistant").split(',')
    pushbullet_token = notifications.get("pushbullet")
    pushover_settings = notifications.get("pushover").split(',')
    items = []
    for item in added_items:
        item = re.sub(r' - <a href.*<\/a>', '', item).replace('<b>', '').replace('</b>', '')
        items.append(item)
    if len(items) > 0:
        cut_items = list(api_request_cutter(items, 5))
        if len(notifications.get("homeassistant")) > 0:
            for cut_item in cut_items:
                homassistant_url = homeassistant_settings[0]
                homeassistant_password = homeassistant_settings[1]
                home_assistant(cut_item, homassistant_url,
                               homeassistant_password)
        if len(notifications.get("pushbullet")) > 0:
            pushbullet(items, pushbullet_token)
        if len(notifications.get('pushover')) > 0:
            for cut_item in cut_items:
                pushover_user = pushover_settings[0]
                pushover_token = pushover_settings[1]
                pushover(cut_item, pushover_user, pushover_token)


def home_assistant(items, homassistant_url, homeassistant_password):
    data = urlencode({
        'title': 'RSScrawler:',
        'body': "\n\n".join(items)
    })

    if six.PY3:
        data = data.encode("utf-8")

    try:
        req = Request(homassistant_url, data)
        req.add_header('X-HA-Access', homeassistant_password)
        req.add_header('Content-Type', 'application/json')
        response = urlopen(req)
    except HTTPError:
        log_debug('FEHLER - Konnte Home Assistant API nicht erreichen')
        return False
    res = json.load(response)
    if res['sender_name']:
        log_debug('Home Assistant Erfolgreich versendet')
    else:
        log_debug('FEHLER - Konnte nicht an Home Assistant Senden')


def pushbullet(items, token):
    data = urlencode({
        'type': 'note',
        'title': 'RSScrawler:',
        'body': "\n\n".join(items)
    })

    if six.PY3:
        data = data.encode("utf-8")

    try:
        req = Request('https://api.pushbullet.com/v2/pushes', data)
        req.add_header('Access-Token', token)
        response = urlopen(req)
    except HTTPError:
        log_debug('FEHLER - Konnte Pushbullet API nicht erreichen')
        return False
    res = json.load(response)
    if res['sender_name']:
        log_debug('Pushbullet Erfolgreich versendet')
    else:
        log_debug('FEHLER - Konnte nicht an Pushbullet Senden')


def pushover(items, pushover_user, pushover_token):
    data = urlencode({
        'user': pushover_user,
        'token': pushover_token,
        'title': 'RSScrawler',
        'message': "\n\n".join(items)
    })
    if six.PY3:
        data = data.encode("utf-8")
    try:
        req = Request('https://api.pushover.net/1/messages.json', data)
        response = urlopen(req)
    except HTTPError:
        log_debug('FEHLER - Konnte Pushover API nicht erreichen')
        return False
    res = json.load(response)
    if res['status'] == 1:
        log_debug('Pushover Erfolgreich versendet')
    else:
        log_debug('FEHLER - Konnte nicht an Pushover Senden')
