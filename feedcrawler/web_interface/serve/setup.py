# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt Hilfsfunktionen für die Ersteinrichtung des FeedCrawlers bereit.

def render_centered_html(inner_content):
    style_outer = """
    display: flex;
    justify-content: center;
    align-items: center; /* Center content vertically */
    height: 100vh;
    max-height: 100vh;
    overflow-y: auto; /* Enable vertical scrolling */
    background-color: #212529;
    color: #fff;
    font-family: system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',
    'Noto Sans','Liberation Sans',Arial,sans-serif,'Apple Color Emoji',
    'Segoe UI Emoji','Segoe UI Symbol','Noto Color Emoji';
    """
    style_inner = """
    background-color: #fff;
    border-radius: 0.375rem;
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
    padding: 20px;
    text-align: center;
    color: #212529;
    font-size: 1rem;
    font-weight: 400;
    line-height: 1.5;
    width: -webkit-fit-content; width: -moz-fit-content; width: fit-content;
    margin: auto; /* Ensure it's centered in the flex container */
    """

    return f'''
    <div style="{style_outer.strip()}">
        <div style="{style_inner.strip()}">
            {inner_content}
        </div>
    </div>
    '''


def render_button(text, button_type="primary", attributes=None):
    base_style = (
        "padding: 0.375rem 0.75rem; font-size: 1rem; line-height: 1.5; "
        "border-radius: 0.375rem; color: #fff; display: inline-block; "
        "font-weight: 400; text-align: center; vertical-align: middle; "
        "cursor: pointer; -webkit-user-select: none; -moz-user-select: none; "
        "user-select: none; transition: color 0.15s ease-in-out, "
        "background-color 0.15s ease-in-out, border-color 0.15s ease-in-out, "
        "box-shadow 0.15s ease-in-out; "
    )

    if button_type == "primary":
        style = base_style + "background-color: #0d6efd; border: 1px solid #0d6efd; "
    else:
        style = base_style + "background-color: #6c757d; border: 1px solid #6c757d; "

    attr_str = ' '.join(f'{key}="{value}"' for key, value in attributes.items()) if attributes else ""

    return f'<button style="{style}" {attr_str}>{text}</button>'


def render_form(header, form="", script=""):
    styles = """
    <style>
        input, select {
            display: block;
            padding: .375rem .75rem;
            width: 100%;
            font-size: 1rem;
            font-weight: 400;
            line-height: 1.5;
            color: #212529;
            background-color: #fff;
            border: 1px solid #dee2e6;
            border-radius: .375rem;
            transition: border-color .15s ease-in-out, box-shadow .15s ease-in-out;
            text-align: center;
            margin: 10px auto;
        }
    </style>
    """
    content = f'''
    <h1>FeedCrawler</h1>
    <h3>{header}</h3>
    {styles}
    {form}
    {script}
    '''
    return render_centered_html(content)


def render_success(message, timeout=10):
    button_html = render_button(f"Wartezeit... {timeout}", "secondary", {"id": "weiterButton", "disabled": "true"})
    script = f"""
                <script>
                    var counter = {timeout};
                    var interval = setInterval(function() {{
                        counter--;
                        document.getElementById('weiterButton').innerText = 'Wartezeit... ' + counter;
                        if (counter === 0) {{
                            clearInterval(interval);
                            document.getElementById('weiterButton').innerText = 'Weiter';
                            document.getElementById('weiterButton').disabled = false;
                            document.getElementById('weiterButton').onclick = function() {{
                                window.location.href='/';
                            }};
                            // Change button style to primary
                            document.getElementById('weiterButton').style.backgroundColor = '#0d6efd'; // Primary button background color
                            document.getElementById('weiterButton').style.borderColor = '#0d6efd'; // Primary button border color
                        }}
                    }}, 1000);
                </script>
                """
    content = f"""<h1>FeedCrawler</h1>
                <h3>{message}</h3>
                {button_html}
                {script}
                """
    return render_centered_html(content)


def render_fail(message):
    button_html = render_button("Zurück", "secondary", {"onclick": "window.location.href='/'"})
    return render_centered_html(f"""<h1>FeedCrawler</h1>
                        <h3>{message}</h3>
                        {button_html}
                        """)
