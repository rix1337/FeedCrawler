# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt alle Funktionen der MyJDAPI in der vom FeedCrawler benötigten Form bereit.

import re
import time

from bs4 import BeautifulSoup

import feedcrawler.myjdapi
from feedcrawler import internal
from feedcrawler.common import check_hoster
from feedcrawler.common import check_is_site
from feedcrawler.common import is_device
from feedcrawler.common import longest_substr
from feedcrawler.common import readable_size
from feedcrawler.common import readable_time
from feedcrawler.common import simplified_search_term_in_title
from feedcrawler.config import CrawlerConfig
from feedcrawler.db import FeedDb
from feedcrawler.url import get_redirected_url
from feedcrawler.url import get_url


def split_urls(urls):
    if isinstance(urls, list):
        return urls
    elif '\\n' in urls:
        urls = urls.split("\\n")
    else:
        urls = urls.split("\n")
    return urls


def ensure_string(potential_list):
    if isinstance(potential_list, list):
        string = ""
        for entry in potential_list:
            string = entry + "\n" + string
        return string
    else:
        string = potential_list
        return string


def get_device():
    conf = CrawlerConfig('FeedCrawler')
    myjd_user = str(conf.get('myjd_user'))
    myjd_pass = str(conf.get('myjd_pass'))
    myjd_device = str(conf.get('myjd_device'))

    jd = feedcrawler.myjdapi.Myjdapi()
    jd.set_app_key('FeedCrawler')

    if myjd_user and myjd_pass and myjd_device:
        try:
            jd.connect(myjd_user, myjd_pass)
            jd.update_devices()
            device = jd.get_device(myjd_device)
        except feedcrawler.myjdapi.MYJDException as e:
            print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
            return False
        if not device or not is_device(device):
            return False
        internal.set_device(device)
        return True
    elif myjd_user and myjd_pass:
        myjd_device = get_if_one_device(myjd_user, myjd_pass)
        try:
            jd.connect(myjd_user, myjd_pass)
            jd.update_devices()
            device = jd.get_device(myjd_device)
        except feedcrawler.myjdapi.MYJDException as e:
            print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
            return False
        if not device or not is_device(device):
            return False
        internal.set_device(device)
        return True
    else:
        return False


def check_device(myjd_user, myjd_pass, myjd_device):
    jd = feedcrawler.myjdapi.Myjdapi()
    jd.set_app_key('FeedCrawler')
    try:
        jd.connect(myjd_user, myjd_pass)
        jd.update_devices()
        device = jd.get_device(myjd_device)
    except feedcrawler.myjdapi.MYJDException as e:
        print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False
    internal.set_device(device)
    return True


def get_if_one_device(myjd_user, myjd_pass):
    jd = feedcrawler.myjdapi.Myjdapi()
    jd.set_app_key('FeedCrawler')
    try:
        jd.connect(myjd_user, myjd_pass)
        jd.update_devices()
        devices = jd.list_devices()
        if len(devices) == 1:
            return devices[0].get('name')
        else:
            return False
    except feedcrawler.myjdapi.MYJDException as e:
        print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def get_packages_in_downloader():
    links = internal.device.downloads.query_links()

    packages = internal.device.downloads.query_packages([{
        "bytesLoaded": True,
        "bytesTotal": True,
        "comment": False,
        "enabled": True,
        "eta": True,
        "priority": False,
        "finished": True,
        "running": True,
        "speed": True,
        "status": True,
        "childCount": True,
        "hosts": True,
        "saveTo": True,
        "maxResults": -1,
        "startAt": 0,
    }])

    if links and packages and len(packages) > 0:
        packages_by_type = check_packages_types(links, packages)
        failed = packages_by_type[0]
        offline = packages_by_type[1]
        decrypted = packages_by_type[2]

        return [failed, offline, decrypted]
    else:
        return [False, False, False]


def get_packages_in_linkgrabber():
    links = internal.device.linkgrabber.query_links()

    packages = internal.device.linkgrabber.query_packages(params=[
        {
            "bytesLoaded": True,
            "bytesTotal": True,
            "comment": True,
            "enabled": True,
            "eta": True,
            "priority": False,
            "finished": True,
            "running": True,
            "speed": True,
            "status": True,
            "childCount": True,
            "hosts": True,
            "saveTo": True,
            "maxResults": -1,
            "startAt": 0,
        }])
    if links and packages and len(packages) > 0:
        packages_by_type = check_packages_types(links, packages)
        failed = packages_by_type[0]
        offline = packages_by_type[1]
        decrypted = packages_by_type[2]

        return [failed, offline, decrypted]
    else:
        return [False, False, False]


def check_packages_types(links, packages):
    decrypted = []
    failed = []
    offline = []
    for package in packages:
        name = package.get('name')
        total_links = package.get('childCount')
        enabled = package.get('enabled')
        size = package.get('bytesTotal')
        done = package.get('bytesLoaded')
        if done and size:
            completed = 100 * done // size
        else:
            completed = 0
        size = readable_size(size)
        done = readable_size(done)
        if not done:
            done = "0"
        speed = package.get('speed')
        if speed:
            speed = readable_size(speed) + "/s"
        hosts = package.get('hosts')
        save_to = package.get('saveTo')
        eta = package.get('eta')
        if eta:
            eta = readable_time(eta)
        uuid = package.get('uuid')
        url = False
        urls = []
        filenames = []
        linkids = []
        package_failed = False
        package_offline = False
        package_online = False
        if links:
            delete_linkids = []
            for link in links:
                if uuid == link.get('packageUUID'):
                    linkid = link.get('uuid')
                    linkids.append(linkid)
                    if link.get('availability') == 'OFFLINE' or link.get(
                            'status') == 'Datei nicht gefunden' or link.get('status') == 'File not found':
                        delete_linkids.append(linkid)
                        package_offline = True
                    elif 'Falscher Captcha Code!' in link.get('name') or 'Wrong Captcha!' in link.get('name') or (
                            link.get('comment') and 'BLOCK_HOSTER' in link.get('comment')):
                        delete_linkids.append(linkid)
                        package_failed = True
                    else:
                        package_online = True
                    url = link.get('url')
                    if url:
                        url = str(url)
                        if url not in urls:
                            urls.append(url)
                        filename = str(link.get('name'))
                        if filename not in filenames:
                            filenames.append(filename)
            if CrawlerConfig("FeedCrawler").get('one_mirror_policy'):
                if delete_linkids:
                    if package_online:
                        remove_from_linkgrabber(delete_linkids, [])
        for h in hosts:
            if h == 'linkcrawlerretry':
                package_failed = True
        status = package.get('status')
        eta_ext = False
        if status:
            if 'fehler' in status.lower() or 'error' in status.lower():
                package_failed = True
            elif "entpacken" in status.lower() or "extracting" in status.lower():
                eta_ext = re.findall(r'eta: (.*?)\)', status, re.IGNORECASE)
                if eta_ext:
                    eta_ext = eta_ext[0].replace("d", "").replace("m", "").replace("s", "")
                if len(eta_ext) == 5:
                    eta_ext = "00:" + eta_ext
                elif len(eta_ext) == 2:
                    eta_ext = "00:00:" + eta_ext
        if package_failed:
            package_offline = False
        if package_failed and not package_offline and len(urls) == 1:
            url = urls[0]
        elif urls:
            urls = "\n".join(urls)
        if package_failed and not package_offline:
            failed.append({"name": name,
                           "path": save_to,
                           "urls": urls,
                           "url": url,
                           "linkids": linkids,
                           "uuid": uuid})
        elif package_offline:
            offline.append({"name": name,
                            "path": save_to,
                            "urls": urls,
                            "linkids": linkids,
                            "uuid": uuid})
        else:
            decrypted.append({"name": name,
                              "links": total_links,
                              "enabled": enabled,
                              "hosts": hosts,
                              "path": save_to,
                              "size": size,
                              "done": done,
                              "percentage": completed,
                              "speed": speed,
                              "eta": eta,
                              "eta_ext": eta_ext,
                              "urls": urls,
                              "filenames": filenames,
                              "linkids": linkids,
                              "uuid": uuid})
    if not failed:
        failed = False
    if not offline:
        offline = False
    if not decrypted:
        decrypted = False
    return [failed, offline, decrypted]


def get_state():
    try:
        if not internal.device or not is_device(internal.device):
            get_device()
        if internal.device:
            try:
                downloader_state = internal.device.downloadcontroller.get_current_state()
                grabber_collecting = internal.device.linkgrabber.is_collecting()
            except feedcrawler.myjdapi.TokenExpiredException:
                get_device()
                if not internal.device or not is_device(internal.device):
                    return False
                downloader_state = internal.device.downloadcontroller.get_current_state()
                grabber_collecting = internal.device.linkgrabber.is_collecting()
            return [True, downloader_state, grabber_collecting]
        else:
            return False
    except feedcrawler.myjdapi.MYJDException as e:
        print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def cryptor_url_first(failed_package):
    resorted_failed_package = []
    for p in failed_package:
        pk = {'name': p['name'], 'path': p['path'], 'urls': p['urls'], 'linkids': p['linkids'], 'uuid': p['uuid']}

        cryptor_found = False
        links = split_urls(pk['urls'])
        for u in links:
            if not cryptor_found:
                if "filecrypt" in u:
                    pk['url'] = u
                    cryptor_found = True
        if not cryptor_found:
            pk['url'] = p['url']

        resorted_failed_package.append(pk)
    return resorted_failed_package


def get_info():
    try:
        if not internal.device or not is_device(internal.device):
            get_device()
        if internal.device:
            try:
                downloader_state = internal.device.downloadcontroller.get_current_state()
                grabber_collecting = internal.device.linkgrabber.is_collecting()
                internal.device.update.run_update_check()
                update_ready = internal.device.update.is_update_available()

                packages_in_downloader = get_packages_in_downloader()
                packages_in_downloader_failed = packages_in_downloader[0]
                packages_in_downloader_offline = packages_in_downloader[1]
                packages_in_downloader_decrypted = packages_in_downloader[2]

                packages_in_linkgrabber = get_packages_in_linkgrabber()
                packages_in_linkgrabber_failed = packages_in_linkgrabber[0]
                packages_in_linkgrabber_offline = packages_in_linkgrabber[1]
                packages_in_linkgrabber_decrypted = packages_in_linkgrabber[2]
            except feedcrawler.myjdapi.TokenExpiredException:
                get_device()
                if not internal.device or not is_device(internal.device):
                    return False
                downloader_state = internal.device.downloadcontroller.get_current_state()
                grabber_collecting = internal.device.linkgrabber.is_collecting()
                internal.device.update.run_update_check()
                update_ready = internal.device.update.is_update_available()

                packages_in_downloader = get_packages_in_downloader()
                packages_in_downloader_failed = packages_in_downloader[0]
                packages_in_downloader_offline = packages_in_downloader[1]
                packages_in_downloader_decrypted = packages_in_downloader[2]

                packages_in_linkgrabber = get_packages_in_linkgrabber()
                packages_in_linkgrabber_failed = packages_in_linkgrabber[0]
                packages_in_linkgrabber_offline = packages_in_linkgrabber[1]
                packages_in_linkgrabber_decrypted = packages_in_linkgrabber[2]

            if packages_in_linkgrabber_failed:
                packages_in_linkgrabber_failed = cryptor_url_first(packages_in_linkgrabber_failed)
            if packages_in_downloader_failed:
                packages_in_downloader_failed = cryptor_url_first(packages_in_downloader_failed)

            if packages_in_downloader_failed and packages_in_linkgrabber_failed:
                packages_failed = packages_in_downloader_failed + packages_in_linkgrabber_failed
            elif packages_in_downloader_failed:
                packages_failed = packages_in_downloader_failed
            else:
                packages_failed = packages_in_linkgrabber_failed

            if packages_in_downloader_offline and packages_in_linkgrabber_offline:
                packages_offline = packages_in_downloader_offline + packages_in_linkgrabber_offline
            elif packages_in_downloader_offline:
                packages_offline = packages_in_downloader_offline
            else:
                packages_offline = packages_in_linkgrabber_offline

            return [True, downloader_state, grabber_collecting, update_ready,
                    [packages_in_downloader_decrypted, packages_in_linkgrabber_decrypted,
                     packages_offline,
                     packages_failed]]
        else:
            return False
    except feedcrawler.myjdapi.MYJDException as e:
        print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def move_to_downloads(linkids, uuid):
    try:
        if not internal.device or not is_device(internal.device):
            get_device()
        if internal.device:
            try:
                internal.device.linkgrabber.move_to_downloadlist(linkids, uuid)
            except feedcrawler.myjdapi.TokenExpiredException:
                get_device()
                if not internal.device or not is_device(internal.device):
                    return False
                internal.device.linkgrabber.move_to_downloadlist(linkids, uuid)
            return True
        else:
            return False
    except feedcrawler.myjdapi.MYJDException as e:
        print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def reset_in_downloads(linkids, uuid):
    try:
        if not internal.device or not is_device(internal.device):
            get_device()
        if internal.device:
            try:
                internal.device.downloads.reset_links(linkids, uuid)
            except feedcrawler.myjdapi.TokenExpiredException:
                get_device()
                if not internal.device or not is_device(internal.device):
                    return False
                internal.device.downloads.reset_links(linkids, uuid)
            return True
        else:
            return False
    except feedcrawler.myjdapi.MYJDException as e:
        print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def remove_from_linkgrabber(linkids, uuid):
    try:
        if not internal.device or not is_device(internal.device):
            get_device()
        if internal.device:
            try:
                internal.device.linkgrabber.remove_links(linkids, uuid)
                internal.device.downloads.remove_links(linkids, uuid)
            except feedcrawler.myjdapi.TokenExpiredException:
                get_device()
                if not internal.device or not is_device(internal.device):
                    return False
                internal.device.linkgrabber.remove_links(linkids, uuid)
                internal.device.downloads.remove_links(linkids, uuid)
            return True
        else:
            return False
    except feedcrawler.myjdapi.MYJDException as e:
        print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def rename_package_in_linkgrabber(package_id, new_name):
    try:
        if not internal.device or not is_device(internal.device):
            get_device()
        if internal.device:
            try:
                internal.device.linkgrabber.rename_package(package_id, new_name)
            except feedcrawler.myjdapi.TokenExpiredException:
                get_device()
                if not internal.device or not is_device(internal.device):
                    return False
                internal.device.linkgrabber.rename_package(package_id, new_name)
            return True
        else:
            return False
    except feedcrawler.myjdapi.MYJDException as e:
        print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def move_to_new_package(linkids, package_id, new_title, new_path):
    try:
        if not internal.device or not is_device(internal.device):
            get_device()
        if internal.device:
            try:
                internal.device.linkgrabber.move_to_new_package(linkids, package_id, new_title, new_path)
                internal.device.downloads.move_to_new_package(linkids, package_id, new_title, new_path)
            except feedcrawler.myjdapi.TokenExpiredException:
                get_device()
                if not internal.device or not is_device(internal.device):
                    return False
                internal.device.linkgrabber.move_to_new_package(linkids, package_id, new_title, new_path)
                internal.device.downloads.move_to_new_package(linkids, package_id, new_title, new_path)
            return True
        else:
            return False
    except feedcrawler.myjdapi.MYJDException as e:
        print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def download(title, subdir, old_links, password, full_path=None, autostart=False):
    try:
        if not internal.device or not is_device(internal.device):
            get_device()

        if isinstance(old_links, list):
            links = []
            for link in old_links:
                if link not in links:
                    links.append(link)
        else:
            links = [old_links]

        links = str(links).replace(" ", "")
        crawljobs = CrawlerConfig('Crawljobs')
        usesubdir = crawljobs.get("subdir")
        priority = "DEFAULT"

        if full_path:
            path = full_path
        else:
            if usesubdir:
                path = subdir + "/<jd:packagename>"
            else:
                path = "<jd:packagename>"
        if "Remux" in path:
            priority = "LOWER"

        try:
            internal.device.linkgrabber.add_links(params=[
                {
                    "autostart": autostart,
                    "links": links,
                    "packageName": title,
                    "extractPassword": password,
                    "priority": priority,
                    "downloadPassword": password,
                    "destinationFolder": path,
                    "comment": "FeedCrawler by rix1337",
                    "overwritePackagizerRules": False
                }])
        except feedcrawler.myjdapi.TokenExpiredException:
            get_device()
            if not internal.device or not is_device(internal.device):
                return False
            internal.device.linkgrabber.add_links(params=[
                {
                    "autostart": autostart,
                    "links": links,
                    "packageName": title,
                    "extractPassword": password,
                    "priority": priority,
                    "downloadPassword": password,
                    "destinationFolder": path,
                    "comment": "FeedCrawler by rix1337",
                    "overwritePackagizerRules": False
                }])
        db = FeedDb('crawldog')
        if db.retrieve(title):
            db.delete(title)
            db.store(title, 'retried')
        else:
            db.store(title, 'added')
        return True
    except feedcrawler.myjdapi.MYJDException as e:
        print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def retry_decrypt(linkids, uuid, links):
    try:
        if not internal.device or not is_device(internal.device):
            get_device()
        if internal.device:
            try:
                package = internal.device.linkgrabber.query_packages(params=[
                    {
                        "availableOfflineCount": True,
                        "availableOnlineCount": True,
                        "availableTempUnknownCount": True,
                        "availableUnknownCount": True,
                        "bytesTotal": True,
                        "childCount": True,
                        "comment": True,
                        "enabled": True,
                        "hosts": True,
                        "maxResults": -1,
                        "packageUUIDs": uuid,
                        "priority": True,
                        "saveTo": True,
                        "startAt": 0,
                        "status": True
                    }])
            except feedcrawler.myjdapi.TokenExpiredException:
                get_device()
                if not internal.device or not is_device(internal.device):
                    return False
                package = internal.device.linkgrabber.query_packages(params=[
                    {
                        "availableOfflineCount": True,
                        "availableOnlineCount": True,
                        "availableTempUnknownCount": True,
                        "availableUnknownCount": True,
                        "bytesTotal": True,
                        "childCount": True,
                        "comment": True,
                        "enabled": True,
                        "hosts": True,
                        "maxResults": -1,
                        "packageUUIDs": uuid,
                        "priority": True,
                        "saveTo": True,
                        "startAt": 0,
                        "status": True
                    }])
            if not package:
                try:
                    package = internal.device.downloads.query_packages(params=[
                        {
                            "bytesLoaded": True,
                            "bytesTotal": True,
                            "comment": True,
                            "enabled": True,
                            "eta": True,
                            "priority": True,
                            "finished": True,
                            "running": True,
                            "speed": True,
                            "status": True,
                            "childCount": True,
                            "hosts": True,
                            "saveTo": True,
                            "maxResults": -1,
                            "packageUUIDs": uuid,
                            "startAt": 0,
                        }])
                except feedcrawler.myjdapi.TokenExpiredException:
                    get_device()
                    if not internal.device or not is_device(internal.device):
                        return False
                    package = internal.device.downloads.query_packages(params=[
                        {
                            "bytesLoaded": True,
                            "bytesTotal": True,
                            "comment": True,
                            "enabled": True,
                            "eta": True,
                            "priority": True,
                            "finished": True,
                            "running": True,
                            "speed": True,
                            "status": True,
                            "childCount": True,
                            "hosts": True,
                            "saveTo": True,
                            "maxResults": -1,
                            "packageUUIDs": uuid,
                            "startAt": 0,
                        }])
            if package:
                remove_from_linkgrabber(linkids, uuid)
                title = package[0].get('name')
                full_path = package[0].get('saveTo')
                download(title, None, links, None, full_path)
                return True
            else:
                return False
        else:
            return False
    except feedcrawler.myjdapi.MYJDException as e:
        print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def jdownloader_start():
    try:
        if not internal.device or not is_device(internal.device):
            get_device()
        if internal.device:
            try:
                internal.device.downloadcontroller.start_downloads()
            except feedcrawler.myjdapi.TokenExpiredException:
                get_device()
                if not internal.device or not is_device(internal.device):
                    return False
                internal.device.downloadcontroller.start_downloads()
            return True
        else:
            return False
    except feedcrawler.myjdapi.MYJDException as e:
        print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def jdownloader_pause(bl):
    try:
        if not internal.device or not is_device(internal.device):
            get_device()
        if internal.device:
            try:
                internal.device.downloadcontroller.pause_downloads(bl)
            except feedcrawler.myjdapi.TokenExpiredException:
                get_device()
                if not internal.device or not is_device(internal.device):
                    return False
                internal.device.downloadcontroller.pause_downloads(bl)
            return True
        else:
            return False
    except feedcrawler.myjdapi.MYJDException as e:
        print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def jdownloader_stop():
    try:
        if not internal.device or not is_device(internal.device):
            get_device()
        if internal.device:
            try:
                internal.device.downloadcontroller.stop_downloads()
            except feedcrawler.myjdapi.TokenExpiredException:
                get_device()
                if not internal.device or not is_device(internal.device):
                    return False
                internal.device.downloadcontroller.stop_downloads()
            return True
        else:
            return False
    except feedcrawler.myjdapi.MYJDException as e:
        print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def check_failed_link_exists(links):
    failed = get_info()
    if failed[2]:
        time.sleep(5)
        failed = get_info()
    failed_packages = failed[4][3]
    for link in links:
        if failed_packages:
            for package in failed_packages:
                for url in package['urls']:
                    if link == url or url in link or link in url:
                        return [failed[0], package['linkids'], package['uuid'], package['name'], package['path']]
    return False


def myjd_download(title, subdir, links, password):
    if internal.device:
        is_episode = re.findall(r'[\w.\s]*S\d{1,2}(E\d{1,2})[\w.\s]*', title)
        if is_episode:
            exists = check_failed_link_exists(links)
            if exists:
                broken_title = False
                old_title = exists[3]
                old_path = exists[4]
                try:
                    new_episode = is_episode.pop()
                except:
                    broken_title = True
                try:
                    old_episode = re.findall(
                        r'[\w.\s]*(?!S\d{1,2})((?:E\d{1,2}-E\d{1,2})|(?:E\d{1,2}E\d{1,2})|(?:E\d{1,2}-\d{1,2})|(?:E\d{1,2}))[\w.\s]*',
                        old_title).pop()
                    combined_episodes = new_episode + '-' + old_episode
                except:
                    broken_title = True

                if not broken_title:
                    linkids = exists[1]
                    package_id = [exists[2]]
                    new_title = title.replace(new_episode, combined_episodes)
                    new_path = old_path.replace(old_title, new_title)

                    internal.device = move_to_new_package(linkids, package_id, new_title, new_path)
                    FeedDb('crawldog').store(new_title, 'added')
                    FeedDb('crawldog').delete(old_title)
                    return True

        internal.device = download(title, subdir, links, password)
        if internal.device:
            return True
    return False


def remove_unfit_links(decrypted_packages, known_packages, keep_linkids, keep_uuids, delete_linkids,
                       delete_uuids, delete_packages, title):
    title = title.replace(" ", ".")
    path = ''
    for package in decrypted_packages:
        path = package['path']

    if keep_linkids and keep_uuids:
        for k in keep_linkids:
            delete_linkids.remove(k)
        move_to_new_package(keep_linkids, keep_uuids, title, path)
        remove_from_linkgrabber(delete_linkids, delete_uuids)
        return [True, True]
    elif delete_packages and len(delete_packages) < len(decrypted_packages):
        delete_linkids = []
        delete_uuids = []
        for dp in delete_packages:
            for linkid in dp['linkids']:
                delete_linkids.append(linkid)
            delete_uuids.append(dp['uuid'])
            decrypted_packages.remove(dp)
        if delete_linkids and delete_uuids:
            remove_from_linkgrabber(delete_linkids, delete_uuids)

    package_merge_check(decrypted_packages, known_packages)
    return [True, False]


def hoster_check(decrypted_packages, title, known_packages):
    if not decrypted_packages:
        return [False, False]

    delete_packages = []
    delete_linkids = []
    delete_uuids = []
    keep_linkids = []
    keep_uuids = []

    merge_first = package_merge_check(decrypted_packages, known_packages)
    if merge_first:
        decrypted_packages = merge_first[1]

    valid_links = False
    if decrypted_packages:
        i = 0
        for dp in decrypted_packages:
            linkids = dp['linkids']
            for link in linkids:
                delete_linkids.append(link)
            uuid = dp['uuid']
            delete_uuids.append(uuid)
            if uuid not in known_packages:
                delete = True
                links = split_urls(dp['urls'])
                for link in links:
                    if check_hoster(link):
                        try:
                            keep_linkids.append(linkids[i])
                            valid_links = True
                        except:
                            pass
                        if uuid not in keep_uuids:
                            keep_uuids.append(uuid)
                        delete = False
                    i += 1
                if delete:
                    delete_packages.append(dp)

    if valid_links:
        removed = remove_unfit_links(decrypted_packages, known_packages, keep_linkids, keep_uuids,
                                     delete_linkids,
                                     delete_uuids, delete_packages, title)
        return [removed[0], removed[1]]
    return [True, False]


def package_merge_check(decrypted_packages, known_packages):
    mergables = []
    if decrypted_packages:
        mergable = False
        for dp in decrypted_packages:
            if "Verschiedene Dateien" not in dp['name'] and "Various files" not in dp['name']:
                mergable = package_to_merge(dp, decrypted_packages, known_packages)
                if mergable:
                    break
        if mergable:
            if len(mergable[0][0]) > 1:
                if mergable not in mergables:
                    mergables.append(mergable)

    if mergables:
        for m in mergables:
            title = longest_substr(m[0][0])
            uuids = m[0][1]
            linkids = m[0][2]
            do_package_merge(title, uuids, linkids)
            time.sleep(3)
            decrypted_packages = get_info()[4][1]
        return [True, decrypted_packages]
    else:
        return False


def package_to_merge(decrypted_package, decrypted_packages, known_packages):
    title = decrypted_package['name']
    mergable = []
    mergable_titles = []
    mergable_uuids = []
    mergable_linkids = []
    for dp in decrypted_packages:
        if dp['uuid'] not in known_packages:
            dp_title = dp['name']
            if simplified_search_term_in_title(title, dp_title, no_numbers=True):
                mergable_titles.append(dp_title)
                mergable_uuids.append(dp['uuid'])
                for link in dp['linkids']:
                    mergable_linkids.append(link)
            elif "Verschiedene Dateien" in dp['name'] or "Various files" in dp['name']:
                mergable_titles.append(dp_title)
                mergable_uuids.append(dp['uuid'])
                for link in dp['linkids']:
                    mergable_linkids.append(link)

    mergable.append([mergable_titles, mergable_uuids, mergable_linkids])
    mergable.sort()
    return mergable


def do_package_merge(title, uuids, linkids):
    try:
        if not internal.device or not is_device(internal.device):
            get_device()
        if internal.device:
            try:
                move_to_new_package(linkids, uuids, title, "<jd:packagename>")
            except feedcrawler.myjdapi.TokenExpiredException:
                get_device()
                if not internal.device or not is_device(internal.device):
                    return False
                move_to_new_package(linkids, uuids, title, "<jd:packagename>")
            return True
        else:
            return False
    except feedcrawler.myjdapi.MYJDException as e:
        print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def do_add_decrypted(title, password, cnl_packages):
    linkids = []
    uuids = []
    urls = ""
    for cnl_package in cnl_packages:
        for linkid in cnl_package['linkids']:
            linkids.append(linkid)
        uuids.append(cnl_package['uuid'])
        urls = urls + ensure_string(cnl_package['urls']).replace("\n\n", "\n")

    links = ensure_string(urls).replace("\n\n", "\n")
    if remove_from_linkgrabber(linkids, uuids):
        if download(title, "FeedCrawler", links, password):
            print(u"[Click'n'Load-Automatik erfolgreich] - " + title)
            return [True, title]
    return False


def myjd_input(port, user, password, device):
    if user and password and device:
        print(u"Zugangsdaten aus den Parametern übernommen.")
    elif user and password and not device:
        one_device = get_if_one_device(user, password)
        if one_device:
            print(u"Gerätename " + one_device + " automatisch ermittelt.")
    else:
        print(u"Bitte die Zugangsdaten für My JDownloader angeben:")
        user = input("Nutzername/Email:")
        password = input("Passwort:")
        one_device = get_if_one_device(user, password)
        if one_device:
            print(u"Gerätename " + one_device + " automatisch ermittelt.")
        else:
            device = input(u"Gerätename:")
    if not port:
        port = '9090'

    sections = ['FeedCrawler', 'Hostnames', 'Crawljobs', 'Notifications', 'Hosters', 'Ombi', 'ContentAll',
                'ContentShows', 'CustomDJ']
    for section in sections:
        CrawlerConfig(section)
    if port:
        CrawlerConfig('FeedCrawler').save("port", port)

    CrawlerConfig('FeedCrawler').save("myjd_user", user)
    CrawlerConfig('FeedCrawler').save("myjd_pass", password)
    CrawlerConfig('FeedCrawler').save("myjd_device", device)
    if get_device():
        return
    else:
        return False


def add_decrypt(title, link, password):
    try:
        if check_is_site(link):
            hostnames = CrawlerConfig('Hostnames')
            fx = hostnames.get('fx')
            ff = hostnames.get('ff')
            sf = hostnames.get('sf')
            if fx and fx in link:
                result = get_url(link)
                real_link = BeautifulSoup(result, 'html5lib').find("input", {"id": "url"})['value']
                if real_link:
                    if "https://" not in real_link:
                        real_link = "https://" + real_link
                    link = real_link
            if (ff and ff in link) or (sf and sf in link):
                real_link = get_redirected_url(link)
                if real_link:
                    link = real_link

        FeedDb('to_decrypt').store(title, link + '|' + password)
        return True
    except:
        return False
