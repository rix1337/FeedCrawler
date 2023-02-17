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
    telegram_settings = notifications.get("telegram").split(',')
    discord_settings = notifications.get("discord").split(',')
    pushbullet_token = notifications.get("pushbullet")
    pushover_settings = notifications.get("pushover").split(',')
    homeassistant_settings = notifications.get("homeassistant").split(',')

    if len(items) > 0:
        if len(notifications.get("telegram")) > 0:
            telegram_token = telegram_settings[0]
            telegram_chat_id = telegram_settings[1]
            telegram(items, telegram_token, telegram_chat_id)
        if len(notifications.get("discord")) > 0:
            discord_webhook_id = discord_settings[0]
            discord_webhook_token = discord_settings[1]
            discord(items, discord_webhook_id, discord_webhook_token)
        if len(notifications.get("pushbullet")) > 0:
            pushbullet(items, pushbullet_token)
        if len(notifications.get('pushover')) > 0:
            pushover_user = pushover_settings[0]
            pushover_token = pushover_settings[1]
            pushover(items, pushover_user, pushover_token)
        if len(notifications.get("homeassistant")) > 0:
            homassistant_url = homeassistant_settings[0]
            homeassistant_password = homeassistant_settings[1]
            home_assistant(items, homassistant_url, homeassistant_password)


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

        formatted_notification = format_notification(item["text"])

        data = {
            'chat_id': chat_id,
            'text': formatted_notification,
            'parse_mode': 'HTML'
        }
        mode = "/sendMessage"

        if imdb_id:
            poster_link = get_poster_link(imdb_id)
            if poster_link:
                data = {
                    'chat_id': chat_id,
                    'photo': poster_link,
                    'caption': formatted_notification,
                    'parse_mode': 'HTML'
                }
                mode = "/sendPhoto"
        try:
            response = request("https://api.telegram.org/bot" + token + mode, method="POST", json=data)
            res = json.loads(response.text)
            if res['ok']:
                shared_state.logger.debug('Telegram - Erfolgreich versendet')
            else:
                shared_state.logger.debug('FEHLER - Konnte nicht an Telegram Senden')
        except (HTTPError, URLError):
            shared_state.logger.debug('FEHLER - Konnte Telegram API nicht erreichen')
            continue


def discord(items, webhook_id, webhook_token):
    for item in items:
        try:
            imdb_id = item["imdb_id"]
        except KeyError:
            imdb_id = False

        headers = {
            'User-Agent': 'FeedCrawler',
            'Content-Type': 'multipart/form-data'
        }
        formatted_notification = format_notification(item["text"]).replace('<b>', '**').replace('</b>', '**').replace(
            '<a href="', '').replace('">', ' - ').replace('</a>', '')

        data = {
            'content': formatted_notification,
            'username': 'FeedCrawler',
            'avatar_url': 'https://imgur.com/tEi4qtb.png'
        }

        if imdb_id:
            poster_link = get_poster_link(imdb_id)
            if poster_link:
                data = {
                    'content': formatted_notification,
                    'embeds': [
                        {'image':
                             {'url': poster_link}
                         }
                    ],
                    'username': 'FeedCrawler',
                    'avatar_url': 'https://imgur.com/tEi4qtb.png'
                }
            try:
                response = request("https://discord.com/api/webhooks/" + webhook_id + "/" + webhook_token,
                                   method="POST",
                                   json=data, headers=headers)
                if response.status_code == 204:
                    shared_state.logger.debug('Discord - Erfolgreich versendet')
                else:
                    shared_state.logger.debug('FEHLER - Konnte nicht an Discord Senden')
            except (HTTPError, URLError):
                shared_state.logger.debug('FEHLER - Konnte Discord API nicht erreichen')
                continue


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
            res = json.loads(response.text)
            if res['sender_name']:
                shared_state.logger.debug('Pushbullet - Erfolgreich versendet')
            else:
                shared_state.logger.debug('FEHLER - Konnte nicht an Pushbullet Senden')
        except (HTTPError, URLError):
            shared_state.logger.debug('FEHLER - Konnte Pushbullet API nicht erreichen')
            return False


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
            res = json.loads(response.text)
            if res['status'] == 1:
                shared_state.logger.debug('Pushover - Erfolgreich versendet')
            else:
                shared_state.logger.debug('FEHLER - Konnte nicht an Pushover Senden')
        except (HTTPError, URLError):
            shared_state.logger.debug('FEHLER - Konnte Pushover API nicht erreichen')
            return False


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
            res = json.loads(response.text)
            if res['sender_name']:
                shared_state.logger.debug('Home Assistant - Erfolgreich versendet')
            else:
                shared_state.logger.debug('FEHLER - Konnte nicht an Home Assistant Senden')

        except (HTTPError, URLError):
            shared_state.logger.debug('FEHLER - Konnte Home Assistant API nicht erreichen')
            return False
