# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul überwacht und steuert die Pakete, nachdem diese im JDownloader hinzugefügt wurden.

import re
import sys
import time
import traceback

from requests.packages.urllib3 import disable_warnings as disable_request_warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from feedcrawler import internal
from feedcrawler.common import Unbuffered, is_device, longest_substr
from feedcrawler.config import CrawlerConfig
from feedcrawler.db import FeedDb
from feedcrawler.myjd import get_device, get_info, hoster_check, remove_from_linkgrabber, rename_package_in_linkgrabber, \
    move_to_downloads, retry_decrypt, add_decrypt
from feedcrawler.notifiers import notify


def crawldog(global_variables):
    internal.set_globals(global_variables)

    sys.stdout = Unbuffered(sys.stdout)
    disable_request_warnings(InsecureRequestWarning)

    crawljobs = CrawlerConfig('Crawljobs')
    autostart = crawljobs.get("autostart")
    db = FeedDb('crawldog')

    grabber_was_collecting = False

    while True:
        try:
            if not internal.device or not is_device(internal.device):
                get_device()

            myjd_packages = get_info()
            if myjd_packages:
                grabber_collecting = myjd_packages[2]

                if grabber_was_collecting or grabber_collecting:
                    grabber_was_collecting = grabber_collecting
                    time.sleep(5)
                else:
                    packages_in_downloader_decrypted = myjd_packages[4][0]
                    packages_in_linkgrabber_decrypted = myjd_packages[4][1]
                    offline_packages = myjd_packages[4][2]
                    encrypted_packages = myjd_packages[4][3]

                    try:
                        watched_titles = db.retrieve_all_titles()
                    except:
                        watched_titles = False

                    notify_list = []

                    if packages_in_downloader_decrypted or packages_in_linkgrabber_decrypted or offline_packages or encrypted_packages:

                        if watched_titles:
                            for title in watched_titles:
                                if packages_in_downloader_decrypted:
                                    for package in packages_in_downloader_decrypted:
                                        if title[0] in package['name'] or title[0].replace(".", " ") in package['name']:
                                            check = hoster_check([package], title[0], [0])
                                            remove = check[0]
                                            if remove:
                                                db.delete(title[0])

                                if packages_in_linkgrabber_decrypted:
                                    for package in packages_in_linkgrabber_decrypted:
                                        if title[0] in package['name'] or title[0].replace(".", " ") in package['name']:
                                            hoster_check([package], title[0], [0])
                                            episodes = FeedDb('episode_remover').retrieve(title[0])
                                            if episodes:
                                                try:
                                                    episodes = episodes.split("|")
                                                except:
                                                    episodes = [episodes]

                                                delete_linkids = []
                                                keep_linkids = []

                                                season_string = re.findall(r'.*(s\d{1,3}).*', title[0], re.IGNORECASE)[
                                                    0]
                                                if season_string:
                                                    if len(episodes) == 1:
                                                        episode_string = str(episodes[0])
                                                        if len(episodes[0]) == 1:
                                                            episode_string = "0" + episode_string
                                                        replace_string = season_string + "E" + episode_string
                                                        append_package_name = title[0].replace(season_string,
                                                                                               replace_string)
                                                    else:
                                                        episode_from_string = str(episodes[0])
                                                        if len(episodes[0]) == 1:
                                                            episode_from_string = "0" + episode_from_string
                                                        episode_to_string = str(episodes[-1])
                                                        if len(episodes[-1]) == 1:
                                                            episode_to_string = "0" + episode_to_string
                                                        replace_string = season_string + "E" + episode_from_string + "-E" + episode_to_string
                                                        append_package_name = title[0].replace(season_string,
                                                                                               replace_string)
                                                else:
                                                    append_package_name = title[0]

                                                for episode in episodes:
                                                    filenames = package['filenames']
                                                    if len(filenames) > 1:
                                                        fname_episodes = []
                                                        for fname in filenames:
                                                            try:
                                                                if re.match(r'.*S\d{1,3}E\d{1,3}.*', fname,
                                                                            flags=re.IGNORECASE):
                                                                    fname = re.findall(r'S\d{1,3}E(\d{1,3})', fname,
                                                                                       flags=re.IGNORECASE).pop()
                                                                else:
                                                                    fname = fname.replace("hddl8", "").replace("dd51",
                                                                                                               "").replace(
                                                                        "264", "").replace("265",
                                                                                           "")
                                                            except:
                                                                fname = fname.replace("hddl8", "").replace("dd51",
                                                                                                           "").replace(
                                                                    "264", "").replace("265", "")
                                                            fname_episode = "".join(
                                                                re.findall(r'\d+', fname.split(".part")[0]))
                                                            try:
                                                                fname_episodes.append(str(int(fname_episode)))
                                                            except:
                                                                pass
                                                        replacer = longest_substr(fname_episodes)

                                                        new_fname_episodes = []
                                                        for new_ep_fname in fname_episodes:
                                                            try:
                                                                new_fname_episodes.append(
                                                                    str(int(new_ep_fname.replace(replacer, ""))))
                                                            except:
                                                                pass
                                                        replacer = longest_substr(new_fname_episodes)

                                                        newer_fname_episodes = []
                                                        for new_ep_fname in new_fname_episodes:
                                                            try:
                                                                newer_fname_episodes.append(
                                                                    str(int(re.sub(replacer, "", new_ep_fname, 1))))
                                                            except:
                                                                pass

                                                        replacer = longest_substr(newer_fname_episodes)

                                                        even_newer_fname_episodes = []
                                                        for newer_ep_fname in newer_fname_episodes:
                                                            try:
                                                                even_newer_fname_episodes.append(
                                                                    str(int(re.sub(replacer, "", newer_ep_fname, 1))))
                                                            except:
                                                                pass

                                                        if even_newer_fname_episodes:
                                                            fname_episodes = even_newer_fname_episodes
                                                        elif newer_fname_episodes:
                                                            fname_episodes = newer_fname_episodes
                                                        elif new_fname_episodes:
                                                            fname_episodes = new_fname_episodes

                                                        pos = 0
                                                        for keep_id in package['linkids']:
                                                            if str(episode) == str(fname_episodes[pos]):
                                                                keep_linkids.append(keep_id)
                                                            pos += 1

                                                for delete_id in package['linkids']:
                                                    if delete_id not in keep_linkids:
                                                        delete_linkids.append(delete_id)

                                                if delete_linkids:
                                                    delete_uuids = [package['uuid']]
                                                    FeedDb('episode_remover').delete(title[0])
                                                    remove_from_linkgrabber(delete_linkids, delete_uuids)
                                                    try:
                                                        new_myjd_packages = get_info()[4][1]
                                                        for new_myjd_package in new_myjd_packages:
                                                            if new_myjd_package["name"] == title[0]:
                                                                package = new_myjd_package
                                                                break
                                                    except:
                                                        pass
                                                rename_package_in_linkgrabber(package['uuid'], append_package_name)
                                            if autostart:
                                                move_to_downloads(package['linkids'],
                                                                  [package['uuid']])
                                            db.delete(title[0])

                                if offline_packages:
                                    for package in offline_packages:
                                        if title[0] in package['name'] or title[0].replace(".", " ") in package['name']:
                                            notify_list.append("[Offline] - " + title[0])
                                            print((u"[Offline] - " + title[0]))
                                            db.delete(title[0])

                                if encrypted_packages:
                                    for package in encrypted_packages:
                                        if title[0] in package['name'] or title[0].replace(".", " ") in package['name']:
                                            if title[1] == 'added':
                                                if retry_decrypt(package['linkids'],
                                                                 [package['uuid']],
                                                                 package['urls']):
                                                    db.delete(title[0])
                                                    db.store(title[0], 'retried')
                                            else:
                                                add_decrypt(package['name'], package['url'], "")
                                                remove_from_linkgrabber(package['linkids'],
                                                                        [package['uuid']])
                                                notify_list.append("[CAPTCHA zu lösen] - " + title[0])
                                                print(u"[CAPTCHA zu lösen] - " + title[0])
                                                db.delete(title[0])
                    else:
                        if not grabber_collecting:
                            db.reset()

                    if notify_list:
                        notify(notify_list)

                time.sleep(30)
            else:
                print(u"Scheinbar ist der JDownloader nicht erreichbar - bitte prüfen und neustarten!")
        except Exception:
            traceback.print_exc()
            time.sleep(30)
