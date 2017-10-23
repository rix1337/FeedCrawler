# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337
# Enthält Code von:
# https://github.com/Gutz-Pilz/pyLoad-stuff/blob/master/SJ.py

import base64
import logging
import urllib
import urllib2
from rssconfig import RssConfig

try:
    import simplejson as json
except ImportError:
    import json

log_info = logging.info
log_error = logging.error
log_debug = logging.debug

notifications = RssConfig('Notifications')
pushbullet_token = notifications.get("pushbullet")
pushover_settings = notifications.get("pushover").split(',')

def api_request_cutter(l, n):
    for i in range(0, len(l), n):
        yield l[i:i+n]

def notify(added_items):
    items = []
    for item in added_items:
        item = item.replace('[<a href="', '').replace('" target="_blank">Link</a>]', '')
        items.append(item.encode('ascii', 'replace'))

    if len(items) > 0:

        cut_items = list(api_request_cutter(items, 5))
        if len(notifications.get("pushbullet")) > 0:
                Pushbullet(items)
        if len(notifications.get('pushover')) > 0:
            for cut_item in cut_items:
                pushover_user = pushover_settings[0]
                pushover_token = pushover_settings[1]
                Pushover(cut_item, pushover_user, pushover_token)

def Pushbullet(items):
    data = urllib.urlencode({
        'type': 'note',
        'title': 'RSScrawler:',
        'body': "\n\n".join(items)
    })
    auth = base64.encodestring('%s:' %pushbullet_token).replace('\n', '')
    try:
        req = urllib2.Request('https://api.pushbullet.com/v2/pushes', data)
        req.add_header('Authorization', 'Basic %s' % auth)
        response = urllib2.urlopen(req)
    except urllib2.HTTPError:
        log_debug('FEHLER - Konnte Pushbullet API nicht erreichen')
        return False
    res = json.load(response)
    if res['sender_name']:
        log_debug('Pushbullet Erfolgreich versendet')
    else:
        log_debug('FEHLER - Konnte nicht an Pushbullet Senden')

def Pushover(items, pushover_user, pushover_token):
    data = urllib.urlencode({
        'user': pushover_user,
        'token': pushover_token,
        'title': 'RSScrawler',
        'message': "\n\n".join(items)
    })
    try:
        req = urllib2.Request('https://api.pushover.net/1/messages.json', data)
        response = urllib2.urlopen(req)
    except urllib2.HTTPError:
        log_debug('FEHLER - Konnte Pushover API nicht erreichen')
        return False
    res = json.load(response)
    if res['status'] == 1:
        log_debug('Pushover Erfolgreich versendet')
    else:
        log_debug('FEHLER - Konnte nicht an Pushover Senden')
