# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337
# Enthält Code von:
# https://github.com/Gutz-Pilz/pyLoad-stuff/blob/master/SJ.py

from future import standard_library
standard_library.install_aliases()
from builtins import range
import base64
import logging
import re
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse

from rssconfig import RssConfig

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


def notify(added_items):
    notifications = RssConfig('Notifications')
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
                Homeassistant(cut_item, homassistant_url,
                              homeassistant_password)
        if len(notifications.get("pushbullet")) > 0:
            Pushbullet(items, pushbullet_token)
        if len(notifications.get('pushover')) > 0:
            for cut_item in cut_items:
                pushover_user = pushover_settings[0]
                pushover_token = pushover_settings[1]
                Pushover(cut_item, pushover_user, pushover_token)


def Homeassistant(items, homassistant_url, homeassistant_password):
    data = urllib.parse.urlencode({
        'title': 'RSScrawler:',
        'body': "\n\n".join(items)
    })
    try:
        req = urllib.request.Request(homassistant_url, data)
        req.add_header('X-HA-Access', homeassistant_password)
        req.add_header('Content-Type', 'application/json')
        response = urllib.request.urlopen(req)
    except urllib.error.HTTPError:
        log_debug('FEHLER - Konnte Home Assistant API nicht erreichen')
        return False
    res = json.load(response)
    if res['sender_name']:
        log_debug('Home Assistant Erfolgreich versendet')
    else:
        log_debug('FEHLER - Konnte nicht an Home Assistant Senden')


def Pushbullet(items, token):
    data = urllib.parse.urlencode({
        'type': 'note',
        'title': 'RSScrawler:',
        'body': "\n\n".join(items)
    })
    auth = base64.encodestring('%s:' % token).replace('\n', '')
    try:
        req = urllib.request.Request('https://api.pushbullet.com/v2/pushes', data)
        req.add_header('Authorization', 'Basic %s' % auth)
        response = urllib.request.urlopen(req)
    except urllib.error.HTTPError:
        log_debug('FEHLER - Konnte Pushbullet API nicht erreichen')
        return False
    res = json.load(response)
    if res['sender_name']:
        log_debug('Pushbullet Erfolgreich versendet')
    else:
        log_debug('FEHLER - Konnte nicht an Pushbullet Senden')


def Pushover(items, pushover_user, pushover_token):
    data = urllib.parse.urlencode({
        'user': pushover_user,
        'token': pushover_token,
        'title': 'RSScrawler',
        'message': "\n\n".join(items)
    })
    try:
        req = urllib.request.Request('https://api.pushover.net/1/messages.json', data)
        response = urllib.request.urlopen(req)
    except urllib.error.HTTPError:
        log_debug('FEHLER - Konnte Pushover API nicht erreichen')
        return False
    res = json.load(response)
    if res['status'] == 1:
        log_debug('Pushover Erfolgreich versendet')
    else:
        log_debug('FEHLER - Konnte nicht an Pushover Senden')
