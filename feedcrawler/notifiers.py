# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt verschiedene Möglichkeiten zum Versand von Benachrichtigungen bereit.

import json
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen, Request

from feedcrawler import internal
from feedcrawler.config import CrawlerConfig
from feedcrawler.external_sites.shared.imdb import get_poster_link


def notify(items):
    notifications = CrawlerConfig('Notifications', )
    homeassistant_settings = notifications.get("homeassistant").split(',')
    pushbullet_token = notifications.get("pushbullet")
    telegram_settings = notifications.get("telegram").split(',')
    pushover_settings = notifications.get("pushover").split(',')
    if len(items) > 0:
        if len(notifications.get("homeassistant")) > 0:
            homassistant_url = homeassistant_settings[0]
            homeassistant_password = homeassistant_settings[1]
            home_assistant(items, homassistant_url, homeassistant_password)
        if len(notifications.get("pushbullet")) > 0:
            pushbullet(items, pushbullet_token)
        if len(notifications.get("telegram")) > 0:
            telegram_token = telegram_settings[0]
            telegram_chat_id = telegram_settings[1]
            telegram(items, telegram_token, telegram_chat_id)
        if len(notifications.get('pushover')) > 0:
            pushover_user = pushover_settings[0]
            pushover_token = pushover_settings[1]
            pushover(items, pushover_user, pushover_token)


def format_notification(text):
    components = text.split(' - ')
    if len(components) == 5:
        event = "<b>" + components[0].replace('[', '').replace(']', '') + "</b>"
        title = components[1]
        site = components[2].replace('[', '').replace(']', '')
        size = " (" + components[3] + ")" if components[3] != '' else ''
        source = "\n" + '<a href="' + components[4] + '">Quelle (' + site + ')</a>' if components[4] != '' else ''
        return event + "\n" + title + size + source
    else:
        event = "<b>" + components[0].replace('[', '').replace(']', '') + "</b>"
        message = " - ".join(components[1:])
        return event + "\n" + message


def home_assistant(items, homassistant_url, homeassistant_password):
    for item in items:
        data = urlencode({
            'title': 'FeedCrawler:',
            'body': item["text"]
        }).encode("utf-8")

        try:
            req = Request(homassistant_url, data)
            req.add_header('X-HA-Access', homeassistant_password)
            req.add_header('Content-Type', 'application/json')
            response = urlopen(req)
        except HTTPError:
            internal.logger.debug('FEHLER - Konnte Home Assistant API nicht erreichen')
            return False
        res = json.load(response)
        if res['sender_name']:
            internal.logger.debug('Home Assistant Erfolgreich versendet')
        else:
            internal.logger.debug('FEHLER - Konnte nicht an Home Assistant Senden')


def telegram(items, token, chat_id):
    for item in items:
        try:
            imdb_id = item["imdb_id"]
        except KeyError:
            imdb_id = False

        data = urlencode({
            'chat_id': chat_id,
            'text': format_notification(item["text"]),
            'parse_mode': 'HTML'
        }).encode("utf-8")
        mode = "/sendMessage"

        if imdb_id:
            poster_link = get_poster_link(imdb_id)
            if poster_link:
                data = urlencode({
                    'chat_id': chat_id,
                    'photo': poster_link,
                    'caption': format_notification(item["text"]),
                    'parse_mode': 'HTML'
                }).encode("utf-8")
                mode = "/sendPhoto"
        try:
            req = Request("https://api.telegram.org/bot" + token + mode, data)
            response = urlopen(req)
        except HTTPError:
            internal.logger.debug('FEHLER - Konnte Telegram API nicht erreichen')
            continue
        res = json.load(response)
        if res['ok']:
            internal.logger.debug('Telegram Erfolgreich versendet')
        else:
            internal.logger.debug('FEHLER - Konnte nicht an Telegram Senden')


def pushbullet(items, token):
    for item in items:
        data = urlencode({
            'type': 'note',
            'title': 'FeedCrawler:',
            'body': item["text"]
        }).encode("utf-8")

        try:
            req = Request('https://api.pushbullet.com/v2/pushes', data)
            req.add_header('Access-Token', token)
            response = urlopen(req)
        except HTTPError:
            internal.logger.debug('FEHLER - Konnte Pushbullet API nicht erreichen')
            return False
        res = json.load(response)
        if res['sender_name']:
            internal.logger.debug('Pushbullet Erfolgreich versendet')
        else:
            internal.logger.debug('FEHLER - Konnte nicht an Pushbullet Senden')


def pushover(items, pushover_user, pushover_token):
    for item in items:
        data = urlencode({
            'user': pushover_user,
            'token': pushover_token,
            'title': 'FeedCrawler',
            'message': item["text"]
        }).encode("utf-8")
        try:
            req = Request('https://api.pushover.net/1/messages.json', data)
            response = urlopen(req)
        except HTTPError:
            internal.logger.debug('FEHLER - Konnte Pushover API nicht erreichen')
            return False
        res = json.load(response)
        if res['status'] == 1:
            internal.logger.debug('Pushover Erfolgreich versendet')
        else:
            internal.logger.debug('FEHLER - Konnte nicht an Pushover Senden')
