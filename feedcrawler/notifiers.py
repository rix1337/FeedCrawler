# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Enthält Code von:
# https://github.com/Gutz-Pilz/pyLoad-stuff/blob/master/SJ.py

import logging
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen, Request

import simplejson as json

from feedcrawler.config import RssConfig

log_info = logging.info
log_error = logging.error
log_debug = logging.debug


def api_request_cutter(message, n):
    for i in range(0, len(message), n):
        yield message[i:i + n]


def notify(items, configfile):
    notifications = RssConfig('Notifications', configfile)
    homeassistant_settings = notifications.get("homeassistant").split(',')
    pushbullet_token = notifications.get("pushbullet")
    telegram_settings = notifications.get("telegram").split(',')
    pushover_settings = notifications.get("pushover").split(',')
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
        if len(notifications.get("telegram")) > 0:
            for cut_item in cut_items:
                telegram_token = telegram_settings[0]
                telegram_chatid = telegram_settings[1]
                telegram(cut_item, telegram_token, telegram_chatid)
        if len(notifications.get('pushover')) > 0:
            for cut_item in cut_items:
                pushover_user = pushover_settings[0]
                pushover_token = pushover_settings[1]
                pushover(cut_item, pushover_user, pushover_token)


def home_assistant(items, homassistant_url, homeassistant_password):
    data = urlencode({
        'title': 'FeedCrawler:',
        'body': "\n\n".join(items)
    }).encode("utf-8")

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


def telegram(items, token, chatid):
    data = urlencode({
        'chat_id': chatid,
        'text': "\n\n".join(items)
    }).encode("utf-8")

    try:
        req = Request("https://api.telegram.org/bot" + token + "/sendMessage", data)
        response = urlopen(req)
    except HTTPError:
        log_debug('FEHLER - Konnte Telegram API nicht erreichen')
        return False
    res = json.load(response)
    if res['ok']:
        log_debug('Telegram Erfolgreich versendet')
    else:
        log_debug('FEHLER - Konnte nicht an Telegram Senden')


def pushbullet(items, token):
    data = urlencode({
        'type': 'note',
        'title': 'FeedCrawler:',
        'body': "\n\n".join(items)
    }).encode("utf-8")

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
        'title': 'FeedCrawler',
        'message': "\n\n".join(items)
    }).encode("utf-8")
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
