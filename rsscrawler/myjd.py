# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import rsscrawler.myjdapi
from rsscrawler.rssconfig import RssConfig


def readable_size(size):
    size = size // 1048576
    if size < 1024:
        size = str(size) + " MB"
    else:
        size = size // 1024
        size = str(size) + " GB"
    return size


def readable_time(time):
    if time < 0:
        return "-"
    if time < 60:
        time = str(time) + " s"
    elif time < 3600:
        time = time // 60
        time = str(time) + " m"
    else:
        time = time // 3600
        time = str(time) + " h"
    return time


def get_device(configfile, dbfile):
    jd = rsscrawler.myjdapi.Myjdapi()
    jd.set_app_key('RSScrawler')

    conf = RssConfig('RSScrawler', configfile)

    myjd_user = str(conf.get('myjd_user'))
    myjd_pass = str(conf.get('myjd_pass'))
    myjd_device = str(conf.get('myjd_device'))

    # TODO save token/encryption key for reuse
    try:
        jd.connect(myjd_user, myjd_pass)
        jd.update_devices()
        device = jd.get_device(myjd_device)
    except rsscrawler.myjdapi.MYJDException as e:
        print("Fehler bei der Verbindung mit MyJDownloader: " + str(e))
        return False
    return device


def download_link(configfile, title, subdir, links, password):
    device = get_device()

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


def get_packages_in_downloader(device):
    downloader_packages = device.downloads.query_packages([{
        "bytesLoaded": True,
        "bytesTotal": True,
        "comment": False,
        "enabled": False,
        "eta": True,
        "priority": False,
        "finished": True,
        "running": True,
        "speed": True,
        "status": True,
        "childCount": True,
        "hosts": True,
        "saveTo": False,
        "maxResults": -1,
        "startAt": 0,
    }])

    if len(downloader_packages) > 0:
        packages = []
        for package in downloader_packages:
            name = package.get('name')
            links = package.get('childCount')
            size = package.get('bytesTotal')
            done = package.get('bytesLoaded')
            completed = 100 * done // size
            size = readable_size(size)
            done = readable_size(done)
            speed = package.get('speed')
            if speed:
                speed = readable_size(speed) + "/s"
            hosts = package.get('hosts')
            eta = package.get('eta')
            if eta:
                eta = readable_time(eta)
            packages.append({"name": name,
                             "links": links,
                             "hosts": hosts,
                             "size": size,
                             "done": done,
                             "percentage": completed,
                             "speed": speed,
                             "eta": eta})
        return packages
    else:
        return False


def get_packages_in_linkgrabber(device):
    grabber_packages = device.linkgrabber.get_package_count()

    if grabber_packages > 0:
        failed = []
        decrypted = []

        grabbed_packages = device.linkgrabber.query_packages(params=[
            {
                "bytesLoaded": False,
                "bytesTotal": True,
                "comment": False,
                "enabled": False,
                "eta": False,
                "priority": False,
                "finished": False,
                "running": False,
                "speed": False,
                "status": False,
                "childCount": True,
                "hosts": True,
                "saveTo": False,
                "maxResults": -1,
                "startAt": 0,
            }])
        for package in grabbed_packages:
            name = package.get('name')
            links = package.get('childCount')
            size = package.get('bytesTotal')
            if size:
                size = readable_size(size)
            hosts = package.get('hosts')
            decrypt_failed = False
            for h in hosts:
                if h == 'linkcrawlerretry':
                    decrypt_failed = True
            if decrypt_failed:
                failed.append(name)
            else:
                decrypted.append({"name": name,
                                  "links": links,
                                  "hosts": hosts,
                                  "size": size})
        if not failed:
            failed = False
        if not decrypted:
            decrypted = False
        return [failed, decrypted]
    else:
        return [False, False]


def update_jdownloader(configfile, dbfile):
    device = get_device(configfile, dbfile)
    if device:
        device.update.run_update_check()
        update = device.update.is_update_available()
        if update:
            device.update.restart_and_update()


def check_failed_packages(configfile, dbfile):
    device = get_device(configfile, dbfile)
    if device:
        grabber_collecting = device.linkgrabber.is_collecting()
        packages_in_linkgrabber = get_packages_in_linkgrabber(device)
        packages_in_linkgrabber_failed = packages_in_linkgrabber[0]

        return [grabber_collecting, packages_in_linkgrabber_failed]
    else:
        return False


def get_info(configfile, dbfile):
    device = get_device(configfile, dbfile)
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
