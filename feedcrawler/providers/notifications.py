# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt verschiedene Möglichkeiten zum Versand von Benachrichtigungen bereit.

import json
from urllib.error import URLError, HTTPError

from feedcrawler.external_sites.metadata.imdb import get_poster_link
from feedcrawler.providers import shared_state
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.http_requests.request_handler import request


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
        event = "<b>" + components[0].replace('[', '').replace(']', '').replace("/", ' - ') + ":</b>"
        title = components[1]
        site = components[2].replace('[', '').replace(']', '')
        size = "\n<b>Größe:</b> " + components[3] if components[3] != '' else ''
        source = "\n" + '<b>Quelle:</b> <a href="' + components[4] + '">' + site + '</a>' if components[4] != '' else ''
        return event + "\n" + title + size + source
    else:
        event = "<b>" + components[0].replace('[', '').replace(']', '') + ":</b>"
        message = " - ".join(components[1:])
        return event + "\n" + message


# This is the preferred way to send notifications, as it is the only one that supports images.
def telegram(items, token, chat_id):
    for item in items:
        try:
            imdb_id = item["imdb_id"]
        except KeyError:
            imdb_id = False

        data = {
            'chat_id': chat_id,
            'text': format_notification(item["text"]),
            'parse_mode': 'HTML'
        }
        mode = "/sendMessage"

        if imdb_id:
            poster_link = get_poster_link(imdb_id)
            if poster_link:
                data = {
                    'chat_id': chat_id,
                    'photo': poster_link,
                    'caption': format_notification(item["text"]),
                    'parse_mode': 'HTML'
                }
                mode = "/sendPhoto"
        try:
            response = request("https://api.telegram.org/bot" + token + mode, method="POST", json=data)
        except (HTTPError, URLError):
            shared_state.logger.debug('FEHLER - Konnte Telegram API nicht erreichen')
            continue
        res = json.loads(response.text)
        if res['ok']:
            shared_state.logger.debug('Telegram Erfolgreich versendet')
        else:
            shared_state.logger.debug('FEHLER - Konnte nicht an Telegram Senden')


def pushbullet(items, token):
    headers = {
        'Access-Token': token
    }

    for item in items:
        data = {
            'type': 'note',
            'title': 'FeedCrawler:',
            'body': item["text"]
        }

        try:
            response = request('https://api.pushbullet.com/v2/pushes', method="POST", json=data, headers=headers)
        except (HTTPError, URLError):
            shared_state.logger.debug('FEHLER - Konnte Pushbullet API nicht erreichen')
            return False
        res = json.loads(response.text)
        if res['sender_name']:
            shared_state.logger.debug('Pushbullet Erfolgreich versendet')
        else:
            shared_state.logger.debug('FEHLER - Konnte nicht an Pushbullet Senden')


def pushover(items, pushover_user, pushover_token):
    for item in items:
        data = {
            'user': pushover_user,
            'token': pushover_token,
            'title': 'FeedCrawler',
            'message': item["text"]
        }
        try:
            response = request('https://api.pushover.net/1/messages.json', method="POST", json=data)
        except (HTTPError, URLError):
            shared_state.logger.debug('FEHLER - Konnte Pushover API nicht erreichen')
            return False
        res = json.loads(response.text)
        if res['status'] == 1:
            shared_state.logger.debug('Pushover Erfolgreich versendet')
        else:
            shared_state.logger.debug('FEHLER - Konnte nicht an Pushover Senden')


def home_assistant(items, homassistant_url, homeassistant_password):
    headers = {
        'X-HA-Access': homeassistant_password,
        'Content-Type': 'application/json'
    }

    for item in items:
        data = {
            'title': 'FeedCrawler:',
            'body': item["text"]
        }

        try:
            response = request(homassistant_url, method="POST", json=data, headers=headers)
        except (HTTPError, URLError):
            shared_state.logger.debug('FEHLER - Konnte Home Assistant API nicht erreichen')
            return False
        res = json.loads(response.text)
        if res['sender_name']:
            shared_state.logger.debug('Home Assistant Erfolgreich versendet')
        else:
            shared_state.logger.debug('FEHLER - Konnte nicht an Home Assistant Senden')
