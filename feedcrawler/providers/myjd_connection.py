# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt alle Funktionen der MyJDAPI in der vom FeedCrawler benötigten Form bereit.

import re
import time

from bs4 import BeautifulSoup

import feedcrawler.external_tools.myjd_api
from feedcrawler.external_tools.myjd_api import TokenExpiredException, RequestTimeoutException, MYJDException, Jddevice
from feedcrawler.providers import shared_state
from feedcrawler.providers.common_functions import check_hoster
from feedcrawler.providers.common_functions import check_is_site
from feedcrawler.providers.common_functions import is_show
from feedcrawler.providers.common_functions import longest_substr
from feedcrawler.providers.common_functions import readable_size
from feedcrawler.providers.common_functions import readable_time
from feedcrawler.providers.common_functions import simplified_search_term_in_title
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.sqlite_database import FeedDb
from feedcrawler.providers.url_functions import get_redirected_url
from feedcrawler.providers.url_functions import get_url


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


def set_device(myjd_user, myjd_pass, myjd_device):
    jd = feedcrawler.external_tools.myjd_api.Myjdapi()
    jd.set_app_key('FeedCrawler')
    try:
        jd.connect(myjd_user, myjd_pass)
        jd.update_devices()
        device = jd.get_device(myjd_device)
    except (TokenExpiredException, RequestTimeoutException, MYJDException) as e:
        print("Fehler bei der Verbindung mit My JDownloader: " + str(e))
        return False
    if not device or not isinstance(device, (type, Jddevice)):
        return False
    else:
        device.downloadcontroller.get_current_state()  # request forces direct_connection info update
        connection_info = device.check_direct_connection()
        if connection_info["status"]:
            print(f"JDownloader direkt über {connection_info['ip']} verfügbar.")
        else:
            print("Keine direkte Verbindung zu JDownloader möglich")
        shared_state.set_device(device)
        return True


def set_device_from_config():
    conf = CrawlerConfig('FeedCrawler')
    myjd_user = str(conf.get('myjd_user'))
    myjd_pass = str(conf.get('myjd_pass'))
    myjd_device = str(conf.get('myjd_device'))

    if myjd_user and myjd_pass and myjd_device:
        return set_device(myjd_user, myjd_pass, myjd_device)
    return False


def get_devices(myjd_user, myjd_pass):
    jd = feedcrawler.external_tools.myjd_api.Myjdapi()
    jd.set_app_key('FeedCrawler')
    try:
        jd.connect(myjd_user, myjd_pass)
        jd.update_devices()
        devices = jd.list_devices()
        return devices
    except (TokenExpiredException, RequestTimeoutException, MYJDException) as e:
        print("Fehler bei der Verbindung mit My JDownloader: " + str(e))
        return []


def get_packages_in_downloader():
    links = shared_state.get_device().downloads.query_links()

    packages = shared_state.get_device().downloads.query_packages([{
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
    links = shared_state.get_device().linkgrabber.query_links()

    packages = shared_state.get_device().linkgrabber.query_packages(params=[
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
        zero_byte_files = []
        package_failed = False
        package_offline = False
        package_online = False
        if links:
            delete_linkids = []
            for link in links:
                if uuid == link.get('packageUUID'):
                    linkid = link.get('uuid')
                    linkids.append(linkid)
                    link_status = link.get('status')
                    if not link_status:
                        link_status = ""

                    if ('Datei nicht gefunden' in link_status or 'File not found' in link_status) and \
                            link.get("bytesTotal") == 0:
                        shared_state.logger.debug("Datei mit 0 Bytes als fertig markiert! " + str(link.get('name')))
                        zero_byte_files.append(linkid)
                        package_failed = True
                    elif link.get(
                            'availability') == 'OFFLINE' or 'Datei nicht gefunden' in link_status or \
                            'File not found' in link_status:
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
                        urls.append(str(url))
                        filename = str(link.get('name'))
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
                           "uuid": uuid,
                           "zero_byte_files": zero_byte_files})
        elif package_offline:
            offline.append({"name": name,
                            "path": save_to,
                            "urls": urls,
                            "linkids": linkids,
                            "uuid": uuid,
                            "zero_byte_files": zero_byte_files})
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
                              "uuid": uuid,
                              "zero_byte_files": zero_byte_files})
    if not failed:
        failed = False
    if not offline:
        offline = False
    if not decrypted:
        decrypted = False
    return [failed, offline, decrypted]


def get_state():
    try:
        if not shared_state.get_device():
            set_device_from_config()
        if shared_state.get_device():
            try:
                downloader_state = shared_state.get_device().downloadcontroller.get_current_state()
                grabber_collecting = shared_state.get_device().linkgrabber.is_collecting()
            except (TokenExpiredException, RequestTimeoutException, MYJDException):
                set_device_from_config()
                if not shared_state.get_device():
                    return False
                downloader_state = shared_state.get_device().downloadcontroller.get_current_state()
                grabber_collecting = shared_state.get_device().linkgrabber.is_collecting()
            return [True, downloader_state, grabber_collecting]
        else:
            return False
    except (TokenExpiredException, RequestTimeoutException, MYJDException) as e:
        print("Fehler bei der Verbindung mit My JDownloader: " + str(e))
        return False


def cryptor_url_first(failed_package):
    resorted_failed_package = []
    for p in failed_package:
        pk = {
            'name': p['name'],
            'path': p['path'],
            'urls': p['urls'],
            'linkids': p['linkids'],
            'uuid': p['uuid'],
            'zero_byte_files': p['zero_byte_files']
        }

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
    def fetch_device_info():
        state = shared_state.get_device().downloadcontroller.get_current_state()
        collecting = shared_state.get_device().linkgrabber.is_collecting()
        shared_state.get_device().update.run_update_check()
        updatable = shared_state.get_device().update.is_update_available()

        downloader = get_packages_in_downloader()
        linkgrabber = get_packages_in_linkgrabber()

        return state, collecting, updatable, downloader, linkgrabber

    def process_packages(downloader, linkgrabber):
        packages_in_downloader_failed, packages_in_downloader_offline, packages_in_downloader_decrypted = downloader
        packages_in_linkgrabber_failed, packages_in_linkgrabber_offline, packages_in_linkgrabber_decrypted = linkgrabber

        if packages_in_linkgrabber_failed:
            packages_in_linkgrabber_failed = cryptor_url_first(packages_in_linkgrabber_failed)
        if packages_in_downloader_failed:
            packages_in_downloader_failed = cryptor_url_first(packages_in_downloader_failed)

        packages_failed = (packages_in_downloader_failed + packages_in_linkgrabber_failed
                           if packages_in_downloader_failed and packages_in_linkgrabber_failed
                           else packages_in_downloader_failed or packages_in_linkgrabber_failed)

        packages_offline = (packages_in_downloader_offline + packages_in_linkgrabber_offline
                            if packages_in_downloader_offline and packages_in_linkgrabber_offline
                            else packages_in_downloader_offline or packages_in_linkgrabber_offline)

        return [packages_in_downloader_decrypted, packages_in_linkgrabber_decrypted, packages_offline, packages_failed]

    try:
        if not shared_state.get_device():
            set_device_from_config()
        if shared_state.get_device():
            try:
                jd_state, jd_collecting, jd_updatable, jd_downloader, jd_linkgrabber = fetch_device_info()
            except (TokenExpiredException, RequestTimeoutException, MYJDException):
                set_device_from_config()
                if not shared_state.get_device():
                    return False
                jd_state, jd_collecting, jd_updatable, jd_downloader, jd_linkgrabber = fetch_device_info()

            packages_info = process_packages(jd_downloader, jd_linkgrabber)
            return [True, jd_state, jd_collecting, jd_updatable, packages_info]
        else:
            return False
    except (TokenExpiredException, RequestTimeoutException, MYJDException) as e:
        print(f"Fehler bei der Verbindung mit My JDownloader: {e}")
        return False


def set_enabled(enable, linkids, uuid):
    def set_enabled_for_device():
        shared_state.get_device().downloads.set_enabled(enable, linkids, uuid)
        shared_state.get_device().linkgrabber.set_enabled(enable, linkids, uuid)

    try:
        if not shared_state.get_device():
            set_device_from_config()
        if shared_state.get_device():
            try:
                set_enabled_for_device()
            except (TokenExpiredException, RequestTimeoutException, MYJDException):
                set_device_from_config()
                if not shared_state.get_device():
                    return False
                set_enabled_for_device()
            return True
        return False
    except (TokenExpiredException, RequestTimeoutException, MYJDException) as e:
        print(f"Fehler bei der Verbindung mit My JDownloader: {e}")
        return False


def move_to_downloads(linkids, uuid):
    try:
        if not shared_state.get_device():
            set_device_from_config()
        if shared_state.get_device():
            try:
                shared_state.get_device().linkgrabber.move_to_downloadlist(linkids, uuid)
            except (TokenExpiredException, RequestTimeoutException, MYJDException):
                set_device_from_config()
                if not shared_state.get_device():
                    return False
                shared_state.get_device().linkgrabber.move_to_downloadlist(linkids, uuid)
            return True
        else:
            return False
    except (TokenExpiredException, RequestTimeoutException, MYJDException) as e:
        print("Fehler bei der Verbindung mit My JDownloader: " + str(e))
        return False


def reset_in_downloads(linkids, uuid):
    try:
        if not shared_state.get_device():
            set_device_from_config()
        if shared_state.get_device():
            try:
                shared_state.get_device().downloads.reset_links(linkids, uuid)
            except (TokenExpiredException, RequestTimeoutException, MYJDException):
                set_device_from_config()
                if not shared_state.get_device():
                    return False
                shared_state.get_device().downloads.reset_links(linkids, uuid)
            return True
        else:
            return False
    except (TokenExpiredException, RequestTimeoutException, MYJDException) as e:
        print("Fehler bei der Verbindung mit My JDownloader: " + str(e))
        return False


def remove_from_linkgrabber(linkids, uuid):
    try:
        if not shared_state.get_device():
            set_device_from_config()
        if shared_state.get_device():
            try:
                shared_state.get_device().linkgrabber.remove_links(linkids, uuid)
                shared_state.get_device().downloads.remove_links(linkids, uuid)
            except (TokenExpiredException, RequestTimeoutException, MYJDException):
                set_device_from_config()
                if not shared_state.get_device():
                    return False
                shared_state.get_device().linkgrabber.remove_links(linkids, uuid)
                shared_state.get_device().downloads.remove_links(linkids, uuid)
            return True
        else:
            return False
    except (TokenExpiredException, RequestTimeoutException, MYJDException) as e:
        print("Fehler bei der Verbindung mit My JDownloader: " + str(e))
        return False


def rename_package_in_linkgrabber(package_id, new_name):
    try:
        if not shared_state.get_device():
            set_device_from_config()
        if shared_state.get_device():
            try:
                shared_state.get_device().linkgrabber.rename_package(package_id, new_name)
            except (TokenExpiredException, RequestTimeoutException, MYJDException):
                set_device_from_config()
                if not shared_state.get_device():
                    return False
                shared_state.get_device().linkgrabber.rename_package(package_id, new_name)
            return True
        else:
            return False
    except (TokenExpiredException, RequestTimeoutException, MYJDException) as e:
        print("Fehler bei der Verbindung mit My JDownloader: " + str(e))
        return False


def move_to_new_package(linkids, package_id, new_title, new_path):
    try:
        if not shared_state.get_device():
            set_device_from_config()
        if shared_state.get_device():
            try:
                shared_state.get_device().linkgrabber.move_to_new_package(linkids, package_id, new_title, new_path)
                shared_state.get_device().downloads.move_to_new_package(linkids, package_id, new_title, new_path)
            except (TokenExpiredException, RequestTimeoutException, MYJDException):
                set_device_from_config()
                if not shared_state.get_device():
                    return False
                shared_state.get_device().linkgrabber.move_to_new_package(linkids, package_id, new_title, new_path)
                shared_state.get_device().downloads.move_to_new_package(linkids, package_id, new_title, new_path)
            return True
        else:
            return False
    except (TokenExpiredException, RequestTimeoutException, MYJDException) as e:
        print("Fehler bei der Verbindung mit My JDownloader: " + str(e))
        return False


def download(title, subdir, old_links, password, full_path=None, autostart=False):
    def add_links_to_linkgrabber(links, path):
        shared_state.get_device().linkgrabber.add_links(params=[
            {
                "autostart": autostart,
                "links": links,
                "packageName": title,
                "extractPassword": password,
                "priority": "DEFAULT",
                "downloadPassword": password,
                "destinationFolder": path,
                "comment": "FeedCrawler by rix1337",
                "overwritePackagizerRules": True
            }
        ])

    try:
        if not shared_state.get_device():
            set_device_from_config()

        download_links = list(set(old_links)) if isinstance(old_links, list) else [old_links]
        download_links = str(download_links).replace(" ", "")

        crawljobs = CrawlerConfig('Crawljobs')
        usesubdir = crawljobs.get("subdir")
        subdir_by_type = crawljobs.get("subdir_by_type")

        if subdir_by_type:
            subdir += "/Serien" if is_show(title) else "/Filme"

        download_path = full_path if full_path else f"{subdir}/<jd:packagename>" if usesubdir else "<jd:packagename>"

        try:
            add_links_to_linkgrabber(download_links, download_path)
        except (TokenExpiredException, RequestTimeoutException, MYJDException):
            set_device_from_config()
            if not shared_state.get_device():
                return False
            add_links_to_linkgrabber(download_links, download_path)

        db = FeedDb('crawldog')
        if db.retrieve(title):
            db.delete(title)
            db.store(title, 'retried')
        else:
            db.store(title, 'added')
        return True
    except (TokenExpiredException, RequestTimeoutException, MYJDException) as e:
        print(f"Fehler bei der Verbindung mit My JDownloader: {e}")
        return False


def retry_decrypt(linkids, uuid, links):
    def query_packages_from_linkgrabber():
        return shared_state.get_device().linkgrabber.query_packages(params=[
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
            }
        ])

    def query_packages_from_downloads():
        return shared_state.get_device().downloads.query_packages(params=[
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
            }
        ])

    def handle_exception():
        set_device_from_config()
        if not shared_state.get_device():
            return False
        return True

    try:
        if not shared_state.get_device():
            set_device_from_config()
        if shared_state.get_device():
            try:
                package = query_packages_from_linkgrabber()
            except (TokenExpiredException, RequestTimeoutException, MYJDException):
                if not handle_exception():
                    return False
                package = query_packages_from_linkgrabber()

            if not package:
                try:
                    package = query_packages_from_downloads()
                except (TokenExpiredException, RequestTimeoutException, MYJDException):
                    if not handle_exception():
                        return False
                    package = query_packages_from_downloads()

            if package:
                remove_from_linkgrabber(linkids, uuid)
                title = package[0].get('name')
                full_path = package[0].get('saveTo')
                if download(title, None, links, None, full_path):
                    return True
            return False
        return False
    except (TokenExpiredException, RequestTimeoutException, MYJDException) as e:
        print(f"Fehler bei der Verbindung mit My JDownloader: {e}")
        return False


def jdownloader_update():
    try:
        if not shared_state.get_device():
            set_device_from_config()
        if shared_state.get_device():
            try:
                shared_state.get_device().update.restart_and_update()
            except feedcrawler.external_tools.myjd_api.TokenExpiredException:
                set_device_from_config()
                if not shared_state.get_device():
                    return False
                shared_state.get_device().update.restart_and_update()
            return True
        else:
            return False
    except feedcrawler.external_tools.myjd_api.MYJDException as e:
        print("Fehler bei der Verbindung mit My JDownloader: " + str(e))
        return False


def jdownloader_start():
    try:
        if not shared_state.get_device():
            set_device_from_config()
        if shared_state.get_device():
            try:
                shared_state.get_device().downloadcontroller.start_downloads()
            except (TokenExpiredException, RequestTimeoutException, MYJDException):
                set_device_from_config()
                if not shared_state.get_device():
                    return False
                shared_state.get_device().downloadcontroller.start_downloads()
            return True
        else:
            return False
    except (TokenExpiredException, RequestTimeoutException, MYJDException) as e:
        print("Fehler bei der Verbindung mit My JDownloader: " + str(e))
        return False


def jdownloader_pause(boolean):
    try:
        if not shared_state.get_device():
            set_device_from_config()
        if shared_state.get_device():
            try:
                shared_state.get_device().downloadcontroller.pause_downloads(boolean)
            except (TokenExpiredException, RequestTimeoutException, MYJDException):
                set_device_from_config()
                if not shared_state.get_device():
                    return False
                shared_state.get_device().downloadcontroller.pause_downloads(boolean)
            return True
        else:
            return False
    except (TokenExpiredException, RequestTimeoutException, MYJDException) as e:
        print("Fehler bei der Verbindung mit My JDownloader: " + str(e))
        return False


def jdownloader_stop():
    try:
        if not shared_state.get_device():
            set_device_from_config()
        if shared_state.get_device():
            try:
                shared_state.get_device().downloadcontroller.stop_downloads()
            except (TokenExpiredException, RequestTimeoutException, MYJDException):
                set_device_from_config()
                if not shared_state.get_device():
                    return False
                shared_state.get_device().downloadcontroller.stop_downloads()
            return True
        else:
            return False
    except (TokenExpiredException, RequestTimeoutException, MYJDException) as e:
        print("Fehler bei der Verbindung mit My JDownloader: " + str(e))
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
    if shared_state.get_device():
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

                    if move_to_new_package(linkids, package_id, new_title, new_path):
                        FeedDb('crawldog').store(new_title, 'added')
                        FeedDb('crawldog').delete(old_title)
                        return True

        if download(title, subdir, links, password):
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
        if not shared_state.get_device():
            set_device_from_config()
        if shared_state.get_device():
            try:
                move_to_new_package(linkids, uuids, title, "<jd:packagename>")
            except (TokenExpiredException, RequestTimeoutException, MYJDException):
                set_device_from_config()
                if not shared_state.get_device():
                    return False
                move_to_new_package(linkids, uuids, title, "<jd:packagename>")
            return True
        else:
            return False
    except (TokenExpiredException, RequestTimeoutException, MYJDException) as e:
        print("Fehler bei der Verbindung mit My JDownloader: " + str(e))
        return False


def add_for_manual_decryption(title, link, password, replace=False):
    try:
        if check_is_site(link):
            hostnames = CrawlerConfig('Hostnames')
            fx = hostnames.get('fx')
            ff = hostnames.get('ff')
            sf = hostnames.get('sf')
            if fx and fx in link:
                result = get_url(link)
                real_link = BeautifulSoup(result, "html.parser").find("input", {"id": "url"})['value']
                if real_link:
                    if "https://" not in real_link:
                        real_link = "https://" + real_link
                    link = real_link
            if (ff and ff in link) or (sf and sf in link):
                real_link = get_redirected_url(link)
                if real_link:
                    link = real_link

        if replace:
            FeedDb('to_decrypt').delete(title)
        FeedDb('to_decrypt').store(title, link + '|' + password)
        return True
    except:
        return False
