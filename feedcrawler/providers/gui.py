# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt eine GUI für den FeedCrawler bereit.

import os
import platform
import sys
import tkinter as tk
import webbrowser
from tkinter import messagebox

from feedcrawler.providers.version import get_version

if platform.system() == 'Windows':
    font = ('Consolas', 12)
elif platform.system() == 'Linux':
    font = ('Monospace', 12)
else:
    font = ('Monaco', 12)

title = f'FeedCrawler v.{get_version()}'


def get_icon_path():
    base_dir = './feedcrawler'
    if getattr(sys, 'frozen', False):
        base_dir = os.path.join(sys._MEIPASS).replace("\\", "/")

    icon_path = f"{base_dir}/web_interface/vuejs_frontend/dist/favicon.ico"
    return icon_path


def get_tray_icon(show_function, quit_function):
    import pystray  # imported here to avoid crash on headless systems
    from PIL import Image  # transitive dependency of pystray not in requirements.txt

    image = Image.open(get_icon_path())
    menu = (
        pystray.MenuItem('Öffnen/Verstecken', show_function, default=True),
        pystray.MenuItem('Web-Interface', lambda: webbrowser.open("http://localhost:9090")),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem('Beenden', quit_function)
    )

    return pystray.Icon("name", image, f"FeedCrawler {get_version()}", menu)


def set_up_window(window):
    window.iconbitmap(get_icon_path())
    window.resizable(False, False)
    window.configure(bg='grey20')
    window.option_add('*foreground', 'white')
    window.option_add('*Button.foreground', 'black')
    window.option_add('*Entry.foreground', 'white')
    window.option_add('*Entry.background', 'grey30')
    window.option_add('*Listbox.foreground', 'white')
    window.option_add('*Listbox.background', 'grey30')
    window.option_add('*Label.foreground', 'white')
    window.option_add('*Label.background', 'grey20')
    window.option_add('*Frame.background', 'grey20')
    window.option_add('*Text.background', 'grey30')
    window.option_add("*Font", font)


def center_window(window):
    window.update_idletasks()
    width = window.winfo_reqwidth()
    height = window.winfo_reqheight()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f"+{x}+{y}")


def create_main_window():
    root = tk.Tk()
    root.withdraw()

    root.title(title)
    set_up_window(root)

    frame = tk.Frame(root, name='frame')
    frame.pack(fill='both', expand=True)
    output_text = tk.Text(frame, wrap='char', width=100, height=20, name='log')
    output_text.pack(side='left', fill='both', expand=True)
    scrollbar = tk.Scrollbar(frame, orient='vertical', command=output_text.yview)
    scrollbar.pack(side='right', fill='y')
    output_text.config(yscrollcommand=scrollbar.set)

    web_interface_button = tk.Button(root, text="Web-Interface",
                                     command=lambda: webbrowser.open("http://localhost:9090"))
    web_interface_button.pack(side="left", padx=10, pady=10)

    exit_button = tk.Button(root, text="Beenden", command=lambda: quit_window())
    exit_button.pack(side="right", padx=10, pady=10)

    def quit_window(*args):
        if messagebox.askokcancel("Beenden", "FeedCrawler wirklich beenden?"):
            icon.stop()
            root.quit()

    def show_window(*args):
        if root.state() == "normal":
            root.withdraw()
        else:
            root.deiconify()
            root.lift()

    icon = get_tray_icon(show_window, quit_window)

    return root, icon


def main_gui(root, icon, shared_state_dict, shared_state_lock):
    def to_tray():
        root.withdraw()

    try:
        root.deiconify()
        root.protocol("WM_DELETE_WINDOW", to_tray)

        to_tray()
        icon.run_detached()

        def print_from_queue_periodically(shared_state_dict, shared_state_lock):
            print_from_queue(shared_state_dict, shared_state_lock)
            root.after(500, lambda: print_from_queue_periodically(shared_state_dict, shared_state_lock))

        print_from_queue_periodically(shared_state_dict, shared_state_lock)
        center_window(root)
        root.mainloop()

    except KeyboardInterrupt:
        pass


class PrintToGui(object):
    def __init__(self, window, max_lines=1024):
        self.widget = window.nametowidget('frame').nametowidget('log')
        self.max_lines = max_lines
        self.line_count = 0

    def write(self, text):
        try:
            self.widget.config(state="normal")

            actual_line_count = int(self.widget.index('end-1c linestart').split('.')[0])
            if actual_line_count > self.max_lines:
                lines_to_remove = actual_line_count - self.max_lines
                self.widget.delete(1.0, f"{lines_to_remove}.0")

            if text.endswith('\n') and len(text) > 1:
                text = text[:-1]

            self.widget.insert("end", text)
            self.widget.see("end")
            self.widget.update()
            self.widget.config(state="disabled")
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
                if data != '\n':
                    if data.endswith('\n'):
                        data = data[:-1]
                self.stream.write(data)
                self.stream.flush()

            def writelines(self, datas):
                self.stream.writelines(datas)
                self.stream.flush()

            def __getattr__(self, attr):
                return getattr(self.stream, attr)

        self.terminal = Unbuffered(sys.stdout)
        self.gui = PrintToGui(window)

    def write(self, message):
        self.terminal.write(message)
        self.gui.write(message)

    def flush(self):
        pass


def update_shared_dict_with_lock(shared_dict, shared_lock, key, value):
    shared_lock.acquire()
    try:
        shared_dict[key] = value
    finally:
        shared_lock.release()


class AppendToPrintQueue(object):
    def __init__(self, shared_state_dict, shared_state_lock):
        try:
            self.shared_state_dict = shared_state_dict
            self.shared_state_lock = shared_state_lock
            try:
                self.shared_state_dict["print_queue"]
            except (KeyboardInterrupt, BrokenPipeError):
                pass
            except KeyError:
                update_shared_dict_with_lock(self.shared_state_dict, self.shared_state_lock, "print_queue", '')
        except (KeyboardInterrupt, BrokenPipeError):
            pass

    def write(self, s):
        try:
            update_shared_dict_with_lock(self.shared_state_dict, self.shared_state_lock, "print_queue",
                                         self.shared_state_dict["print_queue"] + s)
        except (KeyboardInterrupt, BrokenPipeError):
            pass

    def flush(self):
        try:
            update_shared_dict_with_lock(self.shared_state_dict, self.shared_state_lock, "print_queue",
                                         self.shared_state_dict["print_queue"] + '')
        except (KeyboardInterrupt, BrokenPipeError):
            pass


def print_from_queue(shared_state_dict, shared_state_lock):
    try:
        output = shared_state_dict["print_queue"]
        if len(output) > 0:
            print(output)
            update_shared_dict_with_lock(shared_state_dict, shared_state_lock, "print_queue", '')
    except KeyError:
        pass
