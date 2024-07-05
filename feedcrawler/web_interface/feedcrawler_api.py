# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt den Webserver der API des FeedCrawlers bereit.

import sys
from io import StringIO

from feedcrawler.providers.common_functions import Unbuffered
from feedcrawler.web_interface.serve.api import app_container

if sys.stdout is None:  # required to allow pyinstaller --noconsole to work
    sys.stdout = StringIO()
if sys.stderr is None:  # required to allow pyinstaller --noconsole to work
    sys.stderr = StringIO()

from feedcrawler.providers import gui
from feedcrawler.providers import version, shared_state


def web_server(shared_state_dict, shared_state_lock):
    if shared_state_dict["gui"]:
        sys.stdout = gui.AppendToPrintQueue(shared_state_dict, shared_state_lock)
    else:
        sys.stdout = Unbuffered(sys.stdout)

    shared_state.set_state(shared_state_dict, shared_state_lock)
    shared_state.set_logger()

    if version.update_check()[0]:
        updateversion = version.update_check()[1]
        print('Update steht bereit (' + updateversion +
              ')! Weitere Informationen unter https://github.com/rix1337/FeedCrawler/releases/latest')

    app_container()
