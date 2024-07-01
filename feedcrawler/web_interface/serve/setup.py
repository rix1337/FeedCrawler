# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt Hilfsfunktionen für die Ersteinrichtung des FeedCrawlers bereit.

def generate_html_response(message, successful=False):
    if successful:
        return f"""<div style="display: flex; justify-content: center; align-items: center; height: 100vh; background-color: rgb(33, 37, 41);">
                    <div style="background-color: white; border-radius: 10px; box-shadow: 0px 0px 10px 2px rgba(0,0,0,0.1); padding: 20px; text-align: center;">
                        <h1>FeedCrawler</h1>
                        <h3>{message}</h3>
                        <button id="weiterButton" disabled>Wartezeit... 10</button>
                        <script>
                            var counter = 10;
                            var interval = setInterval(function() {{
                                counter--;
                                document.getElementById('weiterButton').innerText = 'Wartezeit... ' + counter;
                                if (counter === 0) {{
                                    clearInterval(interval);
                                    document.getElementById('weiterButton').innerText = 'Weiter';
                                    document.getElementById('weiterButton').disabled = false;
                                    document.getElementById('weiterButton').onclick = function() {{
                                        window.location.href='/';
                                    }}
                                }}
                            }}, 1000);
                        </script>
                    </div>
                </div>"""
    else:
        return f"""<div style="display: flex; justify-content: center; align-items: center; height: 100vh; background-color: rgb(33, 37, 41);">
                    <div style="background-color: white; border-radius: 10px; box-shadow: 0px 0px 10px 2px rgba(0,0,0,0.1); padding: 20px; text-align: center;">
                        <h1>FeedCrawler</h1>
                        <h3>{message}</h3>
                        <button onclick="window.location.href='/'">Zurück</button>
                    </div>
                </div>"""


def render_html_template(header, form, script=""):
    return f'''
    <div style="display: flex; justify-content: center; align-items: center; height: 100vh; background-color: rgb(33, 37, 41);">
        <div style="background-color: white; border-radius: 10px; box-shadow: 0px 0px 10px 2px rgba(0,0,0,0.1); padding: 20px; text-align: center;">
            <h1>FeedCrawler</h1>
            <h3>{header}</h3>
            {form}
        </div>
    </div>
    {script}
    '''
