# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import rsscrawler.myjdapi
from rsscrawler.common import readable_size
from rsscrawler.common import readable_time
from rsscrawler.rssconfig import RssConfig


def get_device(configfile):
    jd = rsscrawler.myjdapi.Myjdapi()
    jd.set_app_key('RSScrawler')

    conf = RssConfig('RSScrawler', configfile)

    myjd_user = str(conf.get('myjd_user'))
    myjd_pass = str(conf.get('myjd_pass'))
    myjd_device = str(conf.get('myjd_device'))

    try:
        jd.connect(myjd_user, myjd_pass)
        jd.update_devices()
        device = jd.get_device(myjd_device)
    except rsscrawler.myjdapi.MYJDException as e:
        print("Fehler bei der Verbindung mit MyJDownloader: " + str(e))
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
        print("Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def get_packages_in_downloader(device):
    links = device.downloads.query_links()

    downloader_packages = device.downloads.query_packages([{
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

    if len(downloader_packages) > 0:
        packages = []
        for package in downloader_packages:
            name = package.get('name')
            total_links = package.get('childCount')
            enabled = package.get('enabled')
            size = package.get('bytesTotal')
            done = package.get('bytesLoaded')
            completed = 100 * done // size
            size = readable_size(size)
            done = readable_size(done)
            speed = package.get('speed')
            if speed:
                speed = readable_size(speed) + "/s"
            hosts = package.get('hosts')
            save_to = package.get('saveTo')
            eta = package.get('eta')
            if eta:
                eta = readable_time(eta)
            uuid = package.get('uuid')
            urls = []
            linkids = []
            for link in links:
                if uuid == link.get('packageUUID'):
                    url = link.get('url')
                    if url not in urls:
                        urls.append(url)
                    linkids.append(link.get('uuid'))
            packages.append({"name": name,
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
                             "linkids": linkids,
                             "uuid": uuid})
        return packages
    else:
        return False


def get_packages_in_linkgrabber(device):
    grabber_packages = device.linkgrabber.get_package_count()

    if grabber_packages > 0:
        failed = []
        decrypted = []

        links = device.linkgrabber.query_links()

        grabbed_packages = device.linkgrabber.query_packages(params=[
            {
                "bytesLoaded": False,
                "bytesTotal": True,
                "comment": False,
                "enabled": True,
                "eta": False,
                "priority": False,
                "finished": False,
                "running": False,
                "speed": False,
                "status": True,
                "childCount": True,
                "hosts": True,
                "saveTo": True,
                "maxResults": -1,
                "startAt": 0,
            }])
        for package in grabbed_packages:
            name = package.get('name')
            total_links = package.get('childCount')
            enabled = package.get('enabled')
            size = package.get('bytesTotal')
            if size:
                size = readable_size(size)
            hosts = package.get('hosts')
            save_to = package.get('saveTo')
            uuid = package.get('uuid')
            urls = []
            linkids = []
            for link in links:
                if uuid == link.get('packageUUID'):
                    url = link.get('url')
                    if url not in urls:
                        urls.append(url)
                    linkids.append(link.get('uuid'))
            decrypt_failed = False
            for h in hosts:
                if h == 'linkcrawlerretry':
                    decrypt_failed = True
            if decrypt_failed:
                failed.append({"name": name,
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
                                  "urls": urls,
                                  "linkids": linkids,
                                  "uuid": uuid})
        if not failed:
            failed = False
        if not decrypted:
            decrypted = False
        return [failed, decrypted]
    else:
        return [False, False]


def check_failed_packages(configfile, device):
    try:
        if not device:
            device = get_device(configfile)
        if device:
            grabber_collecting = device.linkgrabber.is_collecting()
            packages_in_linkgrabber = get_packages_in_linkgrabber(device)
            packages_in_linkgrabber_failed = packages_in_linkgrabber[0]

            return [grabber_collecting, packages_in_linkgrabber_failed]
        else:
            return False
    except rsscrawler.myjdapi.MYJDException as e:
        print("Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def get_state(configfile, device):
    try:
        if not device:
            device = get_device(configfile)
        if device:
            downloader_state = device.downloadcontroller.get_current_state()
            grabber_collecting = device.linkgrabber.is_collecting()
            return [downloader_state, grabber_collecting]
        else:
            return False
    except rsscrawler.myjdapi.MYJDException as e:
        print("Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def get_info(configfile, device):
    try:
        if not device:
            device = get_device(configfile)
        if device:
            downloader_state = device.downloadcontroller.get_current_state()
            grabber_collecting = device.linkgrabber.is_collecting()

            packages_in_downloader = get_packages_in_downloader(device)
            packages_in_linkgrabber = get_packages_in_linkgrabber(device)
            packages_in_linkgrabber_failed = packages_in_linkgrabber[0]
            packages_in_linkgrabber_decrypted = packages_in_linkgrabber[1]

            return [downloader_state, grabber_collecting,
                    [packages_in_downloader, packages_in_linkgrabber_decrypted, packages_in_linkgrabber_failed]]
        else:
            return False
    except rsscrawler.myjdapi.MYJDException as e:
        print("Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def move_to_downloads(configfile, device, linkids, uuid):
    try:
        if not device:
            device = get_device(configfile)
        if device:
            device.linkgrabber.move_to_downloadlist(linkids, uuid)
            return True
        else:
            return False
    except rsscrawler.myjdapi.MYJDException as e:
        print("Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def download_link(configfile, device, title, subdir, links, password):
    try:
        if not device:
            device = get_device(configfile)

        links = ",".join(links)
        crawljobs = RssConfig('Crawljobs', configfile)
        autostart = crawljobs.get("autostart")
        usesubdir = crawljobs.get("subdir")
        priority = "DEFAULT"

        if usesubdir:
            subdir = subdir + "/"
        else:
            subdir = ""
        if subdir == "RSScrawler/Remux/":
            priority = "LOWER"

            device.linkgrabber.add_links(params=[
                {
                    "autostart": autostart,
                    "links": links,
                    "packageName": title,
                    "extractPassword": password,
                    "priority": priority,
                    "downloadPassword": password,
                    "destinationFolder": subdir + "<jd:packagename>",
                    "overwritePackagizerRules": False
                }])
            return True
    except rsscrawler.myjdapi.MYJDException as e:
        print("Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def update_jdownloader(configfile, device):
    try:
        if not device:
            device = get_device(configfile)
        if device:
            device.update.run_update_check()
            update = device.update.is_update_available()
            if update:
                device.update.restart_and_update()
            return True
        else:
            return False
    except rsscrawler.myjdapi.MYJDException as e:
        print("Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def jdownloader_start(configfile, device):
    try:
        if not device:
            device = get_device(configfile)
        if device:
            device.downloadcontroller.start_downloads()
            return True
        else:
            return False
    except rsscrawler.myjdapi.MYJDException as e:
        print("Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def jdownloader_pause(configfile, device, bl):
    try:
        if not device:
            device = get_device(configfile)
        if device:
            device.downloadcontroller.pause_downloads(bl)
            return True
        else:
            return False
    except rsscrawler.myjdapi.MYJDException as e:
        print("Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False


def jdownloader_stop(configfile, device):
    try:
        if not device:
            device = get_device(configfile)
        if device:
            device.downloadcontroller.stop_downloads()
            return True
        else:
            return False
    except rsscrawler.myjdapi.MYJDException as e:
        print("Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False
