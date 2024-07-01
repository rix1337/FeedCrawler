# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt den Server der Ersteinrichtung des FeedCrawlers bereit.

import os
import sys
from urllib import parse

from bottle import Bottle, request

import feedcrawler.external_tools
import feedcrawler.web_interface
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.myjd_connection import get_devices
from feedcrawler.providers.myjd_connection import set_device_from_config
from feedcrawler.web_interface.serve.server import Server
from feedcrawler.web_interface.serve.setup import generate_html_response, render_html_template


def path_config(port, local_address):
    app = Bottle()

    current_path = os.path.dirname(os.path.abspath(sys.argv[0]))

    @app.get('/')
    def config_form():
        config_form_html = f'''
            <form action="/api/config" method="post">
                <label for="config_path">Pfad:</label><br>
                <input type="text" id="config_path" name="config_path" placeholder="{current_path}" style="width: 80%; margin-bottom: 10px;"><br>
                <button type="submit">Speichern</button>
            </form>
            '''
        return render_html_template("Wo sollen Einstellungen und Logs abgelegt werden?", config_form_html)

    def set_config_path(config_path):
        config_path_file = "FeedCrawler.conf"

        if not config_path:
            config_path = current_path

        config_path = config_path.replace("\\", "/")
        config_path = config_path[:-1] if config_path.endswith('/') else config_path

        if not os.path.exists(config_path):
            os.makedirs(config_path)

        with open(config_path_file, "w") as f:
            f.write(config_path)

        return config_path

    @app.post("/api/config")
    def set_config():
        config_path = request.forms.get("config_path")
        config_path = set_config_path(config_path)
        feedcrawler.web_interface.serve.server.temp_server_success = True
        return generate_html_response(f"Konfigurationspfad gesetzt auf: {config_path}", True)

    print(f'Starte temporären Webserver unter "{local_address}:{port}".')
    print("Bitte im Webserver den Konfigurationspfad einstellen!")
    return Server(app, listen='0.0.0.0', port=port).serve_temporarily()


def hostnames_config(port, local_address, shared_state):
    app = Bottle()

    @app.get('/')
    def hostname_form():
        hostname_form_html = '''
        <form action="/api/hostnames" method="post">
            {fields}
            <button type="submit">Speichern</button>
        </form>
        '''

        hostname_fields = '''
        <label for="{id}">{label}</label><br>
        <input type="text" id="{id}" name="{id}" placeholder="example.com" style="width: 80%; margin-bottom: 10px;"><br>
        '''

        hostname_form_content = "".join(
            [hostname_fields.format(id=label.lower(), label=label) for label in shared_state.values["sites"]])

        form_html = hostname_form_html.format(fields=hostname_form_content)

        return render_html_template("Mindestens einen Hostnamen konfigurieren", form_html)

    @app.post("/api/hostnames")
    def set_hostnames():
        def extract_domain(url):
            try:
                if '://' not in url:
                    url = 'http://' + url
                result = parse.urlparse(url)
                return result.netloc
            except Exception as e:
                print(f"Error parsing URL {url}: {e}")
                return None

        hostnames = CrawlerConfig('Hostnames')

        hostname_set = False

        for key in shared_state.values["sites"]:
            hostname = request.forms.get(key.lower())
            try:
                hostname = extract_domain(hostname)
            except Exception as e:
                print(f"Error extracting domain from {hostname}: {e}")
                continue

            if hostname:
                hostnames.save(key, hostname)
                hostname_set = True

        if hostname_set:
            feedcrawler.web_interface.serve.server.temp_server_success = True
            return generate_html_response("Mindestens ein Hostnamen konfiguriert!",
                                          True)
        else:
            return generate_html_response("Es wurde kein valider Hostnamen konfiguriert!",
                                          False)

    print(f'Hostnamen nicht konfiguriert. Starte temporären Webserver unter "{local_address}:{port}".')
    print("Bitte im Webserver die Hostnamen konfigurieren!")
    return Server(app, listen='0.0.0.0', port=port).serve_temporarily()


def myjd_config(port, local_address):
    app = Bottle()

    @app.get('/')
    def hostname_form():
        verify_form_html = '''
        <form id="verifyForm" action="/api/verify_myjd" method="post">
            <label for="user">Nutzername/Email</label><br>
            <input type="text" id="user" name="user" placeholder="Username" style="width: 80%; margin-bottom: 10px;"><br>
            <label for="pass">Passwort</label><br>
            <input type="password" id="pass" name="pass" placeholder="Password" style="width: 80%; margin-bottom: 10px;"><br>
            <button id="verifyButton" type="button" onclick="verifyCredentials()">Geräte abrufen</button>
        </form>
        <form action="/api/store_myjd" method="post" id="deviceForm" style="display: none;">
            <input type="hidden" id="hiddenUser" name="user">
            <input type="hidden" id="hiddenPass" name="pass">
            <label for="device">JDownloader</label><br>
            <select id="device" name="device" style="width: 80%; margin-bottom: 10px;"></select><br>
            <button type="submit">Speichern</button>
        </form>
        '''

        verify_script = '''
        <script>
        function verifyCredentials() {
            var user = document.getElementById('user').value;
            var pass = document.getElementById('pass').value;
            fetch('/api/verify_myjd', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({user: user, pass: pass}),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    var select = document.getElementById('device');
                    data.devices.forEach(device => {
                        var opt = document.createElement('option');
                        opt.value = device;
                        opt.innerHTML = device;
                        select.appendChild(opt);
                    });
                    document.getElementById('hiddenUser').value = document.getElementById('user').value;
                    document.getElementById('hiddenPass').value = document.getElementById('pass').value;
                    document.getElementById("verifyButton").style.display = "none";
                    document.getElementById('deviceForm').style.display = 'block';
                } else {
                    alert('Fehler! Bitte die Zugangsdaten überprüfen.');
                }
            })
            .catch((error) => {
                console.error('Error:', error);
            });
        }
        </script>
        '''

        return render_html_template("My-JDownloader-Zugangsdaten konfigurieren", verify_form_html, verify_script)

    @app.post("/api/verify_myjd")
    def verify_myjd():
        data = request.json
        username = data['user']
        password = data['pass']

        devices = get_devices(username, password)
        device_names = []

        if devices:
            for device in devices:
                device_names.append(device['name'])

        if device_names:
            return {"success": True, "devices": device_names}
        else:
            return {"success": False}

    @app.post("/api/store_myjd")
    def store_myjd():
        username = request.forms.get('user')
        password = request.forms.get('pass')
        device = request.forms.get('device')

        config = CrawlerConfig('FeedCrawler')

        if username and password and device:
            config.save('myjd_user', username)
            config.save('myjd_pass', password)
            config.save('myjd_device', device)

            if not set_device_from_config():
                config.save('myjd_user', "")
                config.save('myjd_pass', "")
                config.save('myjd_device', "")
            else:
                feedcrawler.web_interface.serve.server.temp_server_success = True
                return generate_html_response("Zugangsdaten erfolgreich gespeichert!",
                                              True)

        return generate_html_response("Zugangsdaten fehlerhaft!",
                                      False)

    print(
        f'My-JDownloader-Zugangsdaten nicht konfiguriert. Starte temporären Webserver unter "{local_address}:{port}".')
    print("Bitte im Webserver die My-JDownloader-Zugangsdaten konfigurieren!")
    return Server(app, listen='0.0.0.0', port=port).serve_temporarily()
