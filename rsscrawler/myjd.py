# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import re
import time

from rapidfuzz import fuzz

import rsscrawler.myjdapi
from rsscrawler.rsscommon import check_hoster
from rsscrawler.rsscommon import is_device
from rsscrawler.rsscommon import longest_substr
from rsscrawler.rsscommon import readable_size
from rsscrawler.rsscommon import readable_time
from rsscrawler.rssconfig import RssConfig
from rsscrawler.rssdb import RssDb


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


def get_device(configfile):
    conf = RssConfig('RSScrawler', configfile)
    myjd_user = str(conf.get('myjd_user'))
    myjd_pass = str(conf.get('myjd_pass'))
    myjd_device = str(conf.get('myjd_device'))

    jd = rsscrawler.myjdapi.Myjdapi()
    jd.set_app_key('RSScrawler')

    if myjd_user and myjd_pass and myjd_device:
        try:
            jd.connect(myjd_user, myjd_pass)
            jd.update_devices()
            device = jd.get_device(myjd_device)
        except rsscrawler.myjdapi.MYJDException as e:
            print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
            return False
        if not device or not is_device(device):
            return False
        return device
    elif myjd_user and myjd_pass:
        myjd_device = get_if_one_device(myjd_user, myjd_pass)
        try:
            jd.connect(myjd_user, myjd_pass)
            jd.update_devices()
            device = jd.get_device(myjd_device)
        except rsscrawler.myjdapi.MYJDException as e:
            print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
            return False
        if not device or not is_device(device):
            return False
        return device
    else:
        return False


def check_device(myjd_user, myjd_pass, myjd_device):
    jd = rsscrawler.myjdapi.Myjdapi()
    jd.set_app_key('RSScrawler')
    try:
        jd.connect(myjd_user, myjd_pass)
        jd.update_devices()
        device = jd.get_device(myjd_device)
    except rsscrawler.myjdapi.MYJDException as e:
        print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False
    return device


def get_if_one_device(myjd_user, myjd_pass):
    jd = rsscrawler.myjdapi.Myjdapi()
    jd.set_app_key('RSScrawler')
    try:
        jd.connect(myjd_user, myjd_pass)
        jd.update_devices()
        devices = jd.list_devices()
        if len(devices) == 1:
            return devices[0].get('name')
        else:
            return False
    except rsscrawler.myjdapi.MYJDException as e:
        print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def get_packages_in_downloader(configfile, device):
    links = device.downloads.query_links()

    packages = device.downloads.query_packages([{
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
        packages_by_type = check_packages_types(links, packages, configfile, device)
        failed = packages_by_type[0]
        offline = packages_by_type[1]
        decrypted = packages_by_type[2]
        device = packages_by_type[3]
        return [failed, offline, decrypted, device]
    else:
        return [False, False, False, device]


def get_packages_in_linkgrabber(configfile, device):
    links = device.linkgrabber.query_links()

    packages = device.linkgrabber.query_packages(params=[
        {
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
        packages_by_type = check_packages_types(links, packages, configfile, device)
        failed = packages_by_type[0]
        offline = packages_by_type[1]
        decrypted = packages_by_type[2]
        device = packages_by_type[3]
        return [failed, offline, decrypted, device]
    else:
        return [False, False, False, device]


def check_packages_types(links, packages, configfile, device):
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
            if RssConfig("RSScrawler", configfile).get('one_mirror_policy'):
                if delete_linkids:
                    if package_online:
                        device = remove_from_linkgrabber(configfile, device, delete_linkids, [])
        for h in hosts:
            if h == 'linkcrawlerretry':
                package_failed = True
        status = package.get('status')
        if status:
            if 'Ein Fehler ist aufgetreten!' in status or 'An error occurred!' in status:
                package_failed = True
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
    return [failed, offline, decrypted, device]


def get_state(configfile, device):
    try:
        if not device or not is_device(device):
            device = get_device(configfile)
        if device:
            try:
                downloader_state = device.downloadcontroller.get_current_state()
                grabber_collecting = device.linkgrabber.is_collecting()
            except rsscrawler.myjdapi.TokenExpiredException:
                device = get_device(configfile)
                if not device or not is_device(device):
                    return False
                downloader_state = device.downloadcontroller.get_current_state()
                grabber_collecting = device.linkgrabber.is_collecting()
            return [device, downloader_state, grabber_collecting]
        else:
            return False
    except rsscrawler.myjdapi.MYJDException as e:
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


def get_info(configfile, device):
    try:
        if not device or not is_device(device):
            device = get_device(configfile)
        if device:
            try:
                downloader_state = device.downloadcontroller.get_current_state()
                grabber_collecting = device.linkgrabber.is_collecting()
                device.update.run_update_check()
                update_ready = device.update.is_update_available()

                packages_in_downloader = get_packages_in_downloader(configfile, device)
                packages_in_downloader_failed = packages_in_downloader[0]
                packages_in_downloader_offline = packages_in_downloader[1]
                packages_in_downloader_decrypted = packages_in_downloader[2]
                device = packages_in_downloader[3]

                packages_in_linkgrabber = get_packages_in_linkgrabber(configfile, device)
                packages_in_linkgrabber_failed = packages_in_linkgrabber[0]
                packages_in_linkgrabber_offline = packages_in_linkgrabber[1]
                packages_in_linkgrabber_decrypted = packages_in_linkgrabber[2]
                device = packages_in_linkgrabber[3]
            except rsscrawler.myjdapi.TokenExpiredException:
                device = get_device(configfile)
                if not device or not is_device(device):
                    return False
                downloader_state = device.downloadcontroller.get_current_state()
                grabber_collecting = device.linkgrabber.is_collecting()
                device.update.run_update_check()
                update_ready = device.update.is_update_available()

                packages_in_downloader = get_packages_in_downloader(configfile, device)
                packages_in_downloader_failed = packages_in_downloader[0]
                packages_in_downloader_offline = packages_in_downloader[1]
                packages_in_downloader_decrypted = packages_in_downloader[2]
                device = packages_in_downloader[3]

                packages_in_linkgrabber = get_packages_in_linkgrabber(configfile, device)
                packages_in_linkgrabber_failed = packages_in_linkgrabber[0]
                packages_in_linkgrabber_offline = packages_in_linkgrabber[1]
                packages_in_linkgrabber_decrypted = packages_in_linkgrabber[2]
                device = packages_in_linkgrabber[3]

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

            return [device, downloader_state, grabber_collecting, update_ready,
                    [packages_in_downloader_decrypted, packages_in_linkgrabber_decrypted,
                     packages_offline,
                     packages_failed]]
        else:
            return False
    except rsscrawler.myjdapi.MYJDException as e:
        print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def move_to_downloads(configfile, device, linkids, uuid):
    try:
        if not device or not is_device(device):
            device = get_device(configfile)
        if device:
            try:
                device.linkgrabber.move_to_downloadlist(linkids, uuid)
            except rsscrawler.myjdapi.TokenExpiredException:
                device = get_device(configfile)
                if not device or not is_device(device):
                    return False
                device.linkgrabber.move_to_downloadlist(linkids, uuid)
            return device
        else:
            return False
    except rsscrawler.myjdapi.MYJDException as e:
        print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def remove_from_linkgrabber(configfile, device, linkids, uuid):
    try:
        if not device or not is_device(device):
            device = get_device(configfile)
        if device:
            try:
                device.linkgrabber.remove_links(linkids, uuid)
                device.downloads.remove_links(linkids, uuid)
            except rsscrawler.myjdapi.TokenExpiredException:
                device = get_device(configfile)
                if not device or not is_device(device):
                    return False
                device.linkgrabber.remove_links(linkids, uuid)
                device.downloads.remove_links(linkids, uuid)
            return device
        else:
            return False
    except rsscrawler.myjdapi.MYJDException as e:
        print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def move_to_new_package(configfile, device, linkids, package_id, new_title, new_path):
    try:
        if not device or not is_device(device):
            device = get_device(configfile)
        if device:
            try:
                device.linkgrabber.move_to_new_package(linkids, package_id, new_title, new_path)
                device.downloads.move_to_new_package(linkids, package_id, new_title, new_path)
            except rsscrawler.myjdapi.TokenExpiredException:
                device = get_device(configfile)
                if not device or not is_device(device):
                    return False
                device.linkgrabber.move_to_new_package(linkids, package_id, new_title, new_path)
                device.downloads.move_to_new_package(linkids, package_id, new_title, new_path)
            return device
        else:
            return False
    except rsscrawler.myjdapi.MYJDException as e:
        print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def download(configfile, dbfile, device, title, subdir, old_links, password, full_path=None, autostart=False):
    try:
        if not device or not is_device(device):
            device = get_device(configfile)

        if isinstance(old_links, list):
            links = []
            for l in old_links:
                if l not in links:
                    links.append(l)
        else:
            links = [old_links]

        links = str(links).replace(" ", "")
        crawljobs = RssConfig('Crawljobs', configfile)
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
            device.linkgrabber.add_links(params=[
                {
                    "autostart": autostart,
                    "links": links,
                    "packageName": title,
                    "extractPassword": password,
                    "priority": priority,
                    "downloadPassword": password,
                    "destinationFolder": path,
                    "overwritePackagizerRules": False
                }])
        except rsscrawler.myjdapi.TokenExpiredException:
            device = get_device(configfile)
            if not device or not is_device(device):
                return False
            device.linkgrabber.add_links(params=[
                {
                    "autostart": autostart,
                    "links": links,
                    "packageName": title,
                    "extractPassword": password,
                    "priority": priority,
                    "downloadPassword": password,
                    "destinationFolder": path,
                    "overwritePackagizerRules": False
                }])
        db = RssDb(dbfile, 'crawldog')
        if db.retrieve(title):
            db.delete(title)
            db.store(title, 'retried')
        else:
            db.store(title, 'added')
        return device
    except rsscrawler.myjdapi.MYJDException as e:
        print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def retry_decrypt(configfile, dbfile, device, linkids, uuid, links):
    try:
        if not device or not is_device(device):
            device = get_device(configfile)
        if device:
            try:
                package = device.linkgrabber.query_packages(params=[
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
            except rsscrawler.myjdapi.TokenExpiredException:
                device = get_device(configfile)
                if not device or not is_device(device):
                    return False
                package = device.linkgrabber.query_packages(params=[
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
                    package = device.downloads.query_packages(params=[
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
                except rsscrawler.myjdapi.TokenExpiredException:
                    device = get_device(configfile)
                    if not device or not is_device(device):
                        return False
                    package = device.downloads.query_packages(params=[
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
                remove_from_linkgrabber(configfile, device, linkids, uuid)
                title = package[0].get('name')
                full_path = package[0].get('saveTo')
                download(configfile, dbfile, device, title, None, links, None, full_path)
                return device
            else:
                return False
        else:
            return False
    except rsscrawler.myjdapi.MYJDException as e:
        print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def update_jdownloader(configfile, device):
    try:
        if not device or not is_device(device):
            device = get_device(configfile)
        if device:
            try:
                device.update.restart_and_update()
            except rsscrawler.myjdapi.TokenExpiredException:
                device = get_device(configfile)
                if not device or not is_device(device):
                    return False
                device.update.restart_and_update()
            return device
        else:
            return False
    except rsscrawler.myjdapi.MYJDException as e:
        print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def jdownloader_start(configfile, device):
    try:
        if not device or not is_device(device):
            device = get_device(configfile)
        if device:
            try:
                device.downloadcontroller.start_downloads()
            except rsscrawler.myjdapi.TokenExpiredException:
                device = get_device(configfile)
                if not device or not is_device(device):
                    return False
                device.downloadcontroller.start_downloads()
            return device
        else:
            return False
    except rsscrawler.myjdapi.MYJDException as e:
        print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def jdownloader_pause(configfile, device, bl):
    try:
        if not device or not is_device(device):
            device = get_device(configfile)
        if device:
            try:
                device.downloadcontroller.pause_downloads(bl)
            except rsscrawler.myjdapi.TokenExpiredException:
                device = get_device(configfile)
                if not device or not is_device(device):
                    return False
                device.downloadcontroller.pause_downloads(bl)
            return device
        else:
            return False
    except rsscrawler.myjdapi.MYJDException as e:
        print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def jdownloader_stop(configfile, device):
    try:
        if not device or not is_device(device):
            device = get_device(configfile)
        if device:
            try:
                device.downloadcontroller.stop_downloads()
            except rsscrawler.myjdapi.TokenExpiredException:
                device = get_device(configfile)
                if not device or not is_device(device):
                    return False
                device.downloadcontroller.stop_downloads()
            return device
        else:
            return False
    except rsscrawler.myjdapi.MYJDException as e:
        print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def check_failed_link_exists(links, configfile, device):
    failed = get_info(configfile, device)
    if failed[2]:
        time.sleep(5)
        failed = get_info(configfile, device)
    failed_packages = failed[4][3]
    for link in links:
        if failed_packages:
            for package in failed_packages:
                for url in package['urls']:
                    if link == url or url in link or link in url:
                        device = failed[0]
                        return [device, package['linkids'], package['uuid'], package['name'], package['path']]
    return False


def myjd_download(configfile, dbfile, device, title, subdir, links, password):
    if device:
        is_episode = re.findall(r'[\w.\s]*S\d{1,2}(E\d{1,2})[\w.\s]*', title)
        if is_episode:
            exists = check_failed_link_exists(links, configfile, device)
            if exists:
                broken_title = False
                device = exists[0]
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

                    device = move_to_new_package(configfile, device, linkids, package_id, new_title, new_path)
                    RssDb(dbfile, 'crawldog').store(new_title, 'added')
                    RssDb(dbfile, 'crawldog').delete(old_title)
                    return device

        device = download(configfile, dbfile, device, title, subdir, links, password)
        if device:
            return device
    return False


def remove_unfit_links(configfile, device, decrypted_packages, known_packages, keep_linkids, keep_uuids, delete_linkids,
                       delete_uuids, delete_packages, title):
    title = title.replace(" ", ".")
    path = ''
    for package in decrypted_packages:
        path = package['path']

    if keep_linkids and keep_uuids:
        for k in keep_linkids:
            delete_linkids.remove(k)
        device = move_to_new_package(configfile, device, keep_linkids, keep_uuids, title, path)
        device = remove_from_linkgrabber(configfile, device, delete_linkids, delete_uuids)
        return [device, True]
    elif delete_packages and len(delete_packages) < len(decrypted_packages):
        delete_linkids = []
        delete_uuids = []
        for dp in delete_packages:
            for linkid in dp['linkids']:
                delete_linkids.append(linkid)
            delete_uuids.append(dp['uuid'])
            decrypted_packages.remove(dp)
        if delete_linkids and delete_uuids:
            device = remove_from_linkgrabber(configfile, device, delete_linkids, delete_uuids)

    package_merge_check(device, configfile, decrypted_packages, known_packages)
    return [device, False]


def hoster_check(configfile, device, decrypted_packages, title, known_packages):
    if not decrypted_packages:
        return [False, False]

    delete_packages = []
    delete_linkids = []
    delete_uuids = []
    keep_linkids = []
    keep_uuids = []

    merge_first = package_merge_check(device, configfile, decrypted_packages, known_packages)
    if merge_first:
        device = merge_first[0]
        decrypted_packages = merge_first[1]

    valid_links = False
    if decrypted_packages:
        i = 0
        for dp in decrypted_packages:
            linkids = dp['linkids']
            for l in linkids:
                delete_linkids.append(l)
            uuid = dp['uuid']
            delete_uuids.append(uuid)
            if uuid not in known_packages:
                delete = True
                links = split_urls(dp['urls'])
                for link in links:
                    if check_hoster(link, configfile):
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
        removed = remove_unfit_links(configfile, device, decrypted_packages, known_packages, keep_linkids, keep_uuids,
                                     delete_linkids,
                                     delete_uuids, delete_packages, title)
        return [removed[0], removed[1]]
    return [device, False]


def package_merge(configfile, device, decrypted_packages, title, known_packages):
    if not decrypted_packages:
        return [False, False]

    delete_packages = []
    delete_linkids = []
    delete_uuids = []
    keep_linkids = []
    keep_uuids = []

    episodes = re.findall(r'E(\d{1,3})', title)
    more_than_one_episode = False
    valid_links = False

    merge_first = package_merge_check(device, configfile, decrypted_packages, known_packages)
    if merge_first:
        device = merge_first[0]
        decrypted_packages = merge_first[1]

    if episodes:
        int_episodes = []
        for ep in episodes:
            int_episodes.append(int(ep))
        if len(int_episodes) > 1:
            sorted_eps = sorted(int_episodes)
            min_ep = sorted_eps[0]
            max_ep = sorted_eps[-1]
            all_episodes = list(range(min_ep, max_ep + 1))
        else:
            all_episodes = list(int_episodes)
        all_episodes_merged = int("".join(str(int_episode) for int_episode in int_episodes))

        if decrypted_packages:
            fname_episodes = []
            for dp in decrypted_packages:
                if dp['uuid'] not in known_packages:
                    fnames = dp['filenames']
                    for fname in fnames:
                        try:
                            if re.match(r'.*S\d{1,3}E\d{1,3}.*', fname, flags=re.IGNORECASE):
                                fname = re.findall(r'S\d{1,3}E(\d{1,3})', fname, flags=re.IGNORECASE).pop()
                            else:
                                fname = fname.replace("hddl8", "").replace("dd51", "").replace("264", "").replace("265",
                                                                                                                  "")
                        except:
                            fname = fname.replace("hddl8", "").replace("dd51", "").replace("264", "").replace("265", "")
                        fname_episode = "".join(re.findall(r'\d+', fname.split(".part")[0]))
                        fname_episodes.append(str(int(fname_episode)))
            replacer = longest_substr(fname_episodes)

            new_fname_episodes = []
            for new_ep_fname in fname_episodes:
                try:
                    new_fname_episodes.append(str(int(new_ep_fname.replace(replacer, ""))))
                except:
                    pass
            replacer = longest_substr(new_fname_episodes)

            newer_fname_episodes = []
            for new_ep_fname in new_fname_episodes:
                try:
                    newer_fname_episodes.append(str(int(re.sub(replacer, "", new_ep_fname, 1))))
                except:
                    pass

            replacer = longest_substr(newer_fname_episodes)

            even_newer_fname_episodes = []
            for newer_ep_fname in newer_fname_episodes:
                try:
                    even_newer_fname_episodes.append(str(int(re.sub(replacer, "", newer_ep_fname, 1))))
                except:
                    pass

            if even_newer_fname_episodes:
                fname_episodes = even_newer_fname_episodes
            elif not newer_fname_episodes:
                if new_fname_episodes:
                    fname_episode = new_fname_episodes
            else:
                fname_episodes = newer_fname_episodes

            i = 0
            for dp in decrypted_packages:
                linkids = dp['linkids']
                for l in linkids:
                    delete_linkids.append(l)
                uuid = dp['uuid']
                delete_uuids.append(uuid)
                if uuid not in known_packages:
                    delete = True
                    fnames = dp['filenames']
                    for _ in fnames:
                        try:
                            if not fname_episodes[i] == replacer:
                                fname_episode = int(fname_episodes[i])
                                more_than_one_episode = True
                            if fname_episode in all_episodes or fname_episode == all_episodes_merged:
                                keep_linkids.append(linkids[i])
                                if uuid not in keep_uuids:
                                    keep_uuids.append(uuid)
                                delete = False
                        except:
                            pass
                        i += 1
                    if delete:
                        delete_packages.append(dp)
    else:
        if decrypted_packages:
            i = 0
            for dp in decrypted_packages:
                linkids = dp['linkids']
                for l in linkids:
                    delete_linkids.append(l)
                uuid = dp['uuid']
                delete_uuids.append(uuid)
                if uuid not in known_packages:
                    delete = True
                    links = split_urls(dp['urls'])
                    for _ in links:
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

    if more_than_one_episode or valid_links:
        removed = remove_unfit_links(configfile, device, decrypted_packages, known_packages, keep_linkids, keep_uuids,
                                     delete_linkids,
                                     delete_uuids, delete_packages, title)
        return [removed[0], removed[1]]
    return [device, False]


def package_merge_check(device, configfile, decrypted_packages, known_packages):
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
            do_package_merge(configfile, device, title, uuids, linkids)
            time.sleep(3)
            decrypted_packages = get_info(configfile, device)[4][1]
        return [device, decrypted_packages]
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
            ratio = fuzz.partial_ratio(title, dp_title)
            if ratio > 55:
                mergable_titles.append(dp_title)
                mergable_uuids.append(dp['uuid'])
                for l in dp['linkids']:
                    mergable_linkids.append(l)
            elif "Verschiedene Dateien" in dp['name'] or "Various files" in dp['name']:
                mergable_titles.append(dp_title)
                mergable_uuids.append(dp['uuid'])
                for l in dp['linkids']:
                    mergable_linkids.append(l)

    mergable.append([mergable_titles, mergable_uuids, mergable_linkids])
    mergable.sort()
    return mergable


def do_package_merge(configfile, device, title, uuids, linkids):
    try:
        if not device or not is_device(device):
            device = get_device(configfile)
        if device:
            try:
                move_to_new_package(configfile, device, linkids, uuids, title, "<jd:packagename>")
            except rsscrawler.myjdapi.TokenExpiredException:
                device = get_device(configfile)
                if not device or not is_device(device):
                    return False
                move_to_new_package(configfile, device, linkids, uuids, title, "<jd:packagename>")
            return device
        else:
            return False
    except rsscrawler.myjdapi.MYJDException as e:
        print(u"Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def do_package_replace(configfile, dbfile, device, old_package, cnl_package):
    title = old_package['name']
    path = old_package['path']
    links = (ensure_string(old_package['urls']) + '\n' + ensure_string(cnl_package['urls'])).replace("\n\n", "\n")
    links = links.replace(old_package['url'] + '\n', '').replace(old_package['url'], '')
    linkids = cnl_package['linkids']
    uuid = [cnl_package['uuid']]
    device = remove_from_linkgrabber(configfile, device, linkids, uuid)
    if device:
        linkids = old_package['linkids']
        uuid = [old_package['uuid']]
        device = remove_from_linkgrabber(configfile, device, linkids, uuid)
        if device:
            device = download(configfile, dbfile, device, title, "", links, "", path, False)
            if device:
                print(u"[Click'n'Load-Automatik erfolgreich] - " + title)
                return [device, title]
    return False
