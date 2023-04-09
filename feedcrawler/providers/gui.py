# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt eine GUI für den FeedCrawler bereit. Diese setzt die Dependencies PySimpleGUI und psgtray voraus.

import base64
import ctypes
import os
import platform
import sys
import webbrowser

from feedcrawler.providers.version import get_version

try:
    import PySimpleGUI as sg  # not in requirements.txt as we don't want to force users to install it
    from psgtray import SystemTray  # not in requirements.txt as we don't want to force users to install it

    enabled = True
except ImportError:
    enabled = False

if platform.system() == 'Windows':
    font = ('Consolas', 12)
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('FeedCrawler')
elif platform.system() == 'Linux':
    font = ('Monospace', 12)
else:
    font = ('Monaco', 12)

title = 'FeedCrawler v.' + get_version()


def check_gui_enabled(func):
    def wrapper(*args, **kwargs):
        if enabled:
            return func(*args, **kwargs)
        else:
            return False

    return wrapper


def get_icon_path():
    base_dir = './feedcrawler'
    if getattr(sys, 'frozen', False):
        base_dir = os.path.join(sys._MEIPASS).replace("\\", "/")

    icon_path = base_dir + '/web_interface/vuejs_frontend/dist/favicon.ico'
    return icon_path


def get_icon():
    icon_path = get_icon_path()
    with open(icon_path, 'rb') as f:
        icon_data = f.read()
    icon_base64 = base64.b64encode(icon_data)
    return icon_base64


@check_gui_enabled
def create_main_window():
    sg.theme('dark grey 9')
    sg.set_options(font=font)

    layout = [
        [sg.Multiline(size=(100, 20), key="-OUTPUT-", background_color="grey20", text_color="white", font=font,
                      autoscroll=True, )],
        [sg.Button('Web-Interface'), sg.Button('Beenden')],
    ]

    window = sg.Window(title,
                       layout,
                       finalize=True,
                       enable_close_attempted_event=True,
                       element_justification='c',
                       icon=get_icon_path())

    window.hide()

    return window


@check_gui_enabled
def main_gui(window, shared_state_dict):
    if not window:
        print("GUI-Fenster falsch initialisiert.")
        window = create_main_window()
    try:
        menu = ['', [title,
                     '---',
                     'GUI',
                     'Web-Interface',
                     '---',
                     'Beenden']
                ]
        tray = SystemTray(menu, single_click_events=False, window=window, tooltip='Tooltip', icon=get_icon())
        tray.show_message(title, 'Gestartet und im Tray verfügbar.')

        while True:
            event, values = window.read(timeout=500)

            print_from_queue(shared_state_dict)

            if event == tray.key:
                event = values[event]  # use the System Tray's event as if was from the window

            if event in 'Beenden':
                break

            if event in (sg.EVENT_SYSTEM_TRAY_ICON_DOUBLE_CLICKED, 'GUI'):
                window.un_hide()
                window.bring_to_front()
            elif event in title:
                webbrowser.open("https://github.com/rix1337/FeedCrawler")
            elif event in 'Web-Interface':
                webbrowser.open("http://localhost:9090")
            elif event in sg.WIN_CLOSE_ATTEMPTED_EVENT:
                window.hide()

        tray.close()
        window.close()

    except KeyboardInterrupt:
        pass


@check_gui_enabled
def get_devices(myjd_user, myjd_pass):
    import feedcrawler.external_tools.myjd_api
    from feedcrawler.external_tools.myjd_api import TokenExpiredException, RequestTimeoutException, MYJDException

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


@check_gui_enabled
def no_hostnames_gui(configfile):
    # warn user if no hostnames are configured
    sg.theme('dark grey 9')
    layout = [
        [sg.Text('Keine Hostnamen in der FeedCrawler.ini gefunden! Beende FeedCrawler!')],
        [sg.Button('OK', bind_return_key=True)]
    ]

    window = sg.Window('Warnung', layout, finalize=True, element_justification='c', icon=get_icon_path())
    webbrowser.open(configfile)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        window.close()


@check_gui_enabled
def configpath_gui(current_path):
    configpath = ''

    sg.theme('dark grey 9')
    layout = [
        [sg.Button('"' + current_path + '" verwenden', bind_return_key=True)],
        [sg.Input(key='-FOLDER-', enable_events=True, visible=False),
         sg.FolderBrowse('Anderen Pfad wählen', target='-FOLDER-', initial_folder=current_path)]
    ]

    window = sg.Window('Wo sollen Einstellungen und Logs abgelegt werden?', layout, icon=get_icon_path())

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        configpath = values['-FOLDER-']
        window.close()

    if not configpath:
        configpath = ''
    return configpath


@check_gui_enabled
def myjd_credentials_gui():
    user = ''
    password = ''
    device = ''

    sg.theme('dark grey 9')
    layout = [
        [sg.Text('Bitte die Zugangsdaten für My JDownloader angeben:')],
        [sg.Text('Benutzername', size=(15, 1)), sg.InputText(key='username')],
        [sg.Text('Passwort', size=(15, 1)), sg.InputText(key='password', password_char='*')],
        [sg.Button('OK', bind_return_key=True), sg.Button('Abbrechen')]
    ]

    window = sg.Window('My JDownloader Login', layout, finalize=True, element_justification='c', icon=get_icon_path())

    while True:
        event, values = window.read()

        if event in (sg.WIN_CLOSED, 'Abbrechen'):
            window.close()
            break
        elif event in 'OK':
            user = values['username']
            password = values['password']
            if not user or not password:
                sg.popup('Bitte Benutzername und Passwort angeben.')
                continue
            elif user and password:
                devices = get_devices(user, password)
                if not devices:
                    sg.popup('Keine Geräte gefunden. Bitte überprüfe deine Zugangsdaten.')
                    continue
                else:
                    window.hide()
                    device_list = []
                    for dv in devices:
                        device_list.append(dv['name'])

                    layout = [
                        [sg.Text('Bitte den gewünschten JDownloader auswählen:')],
                        [sg.Listbox(values=device_list, size=(20, 5), key='device')],
                        [sg.Button('OK', bind_return_key=True), sg.Button('Abbrechen')]
                    ]
                    device_selection = sg.Window('My JDownloader Gerät', layout, finalize=True,
                                                 element_justification='c',
                                                 icon=get_icon_path())
                    while True:
                        event, values = device_selection.read()

                        if event in (sg.WIN_CLOSED, 'Abbrechen'):
                            device_selection.close()
                            break
                        elif event in 'OK':
                            device = values['device'][0]

                        device_selection.close()
        window.close()

    if not user or not password or not device:
        user = ""
        password = ""
        device = ""
    return user, password, device


class PrintToGui(object):
    def __init__(self, widget, max_lines=999):
        self.widget = widget
        self.max_lines = max_lines
        self.line_count = 0

    def write(self, text):
        try:
            output = self.widget.get()
        except:
            output = ''

        # Split text into individual lines
        lines = text.split('\n')

        # Add each line to the output
        for line in lines:
            if len(line) > 0:
                if self.line_count >= self.max_lines:
                    # Remove oldest line
                    output_lines = output.split('\n')
                    output = '\n'.join(output_lines[1:])
                else:
                    self.line_count += 1
                output += '\n' + line
                if output.startswith('\n'):
                    output = output[1:]

        try:
            self.widget.update(value=output)
        except:
            pass

    def flush(self):
        pass


class PrintToConsoleAndGui(object):
    def __init__(self, window):
        class Unbuffered(object):
            def __init__(self, stream):
                self.stream = stream

            def write(self, data):
                if data != '\n' and data.endswith('\n'):
                    data = data[:-1]
                self.stream.write(data)
                self.stream.flush()

            def writelines(self, datas):
                self.stream.writelines(datas)
                self.stream.flush()

            def __getattr__(self, attr):
                return getattr(self.stream, attr)

        self.terminal = Unbuffered(sys.stdout)
        self.gui = PrintToGui(window['-OUTPUT-'])

    def write(self, message):
        self.terminal.write(message)
        self.gui.write(message)

    def flush(self):
        pass


class AppendToPrintQueue(object):
    def __init__(self, shared_state_dict):
        self.shared_state_dict = shared_state_dict
        try:
            self.shared_state_dict["print_queue"]
        except KeyError:
            self.shared_state_dict["print_queue"] = ''

    def write(self, s):
        self.shared_state_dict["print_queue"] += s

    def flush(self):
        self.shared_state_dict["print_queue"] += ''


def print_from_queue(shared_state_dict):
    try:
        output = shared_state_dict["print_queue"]
        if len(output) > 0:
            print(output)
            shared_state_dict["print_queue"] = ''
    except KeyError:
        pass
