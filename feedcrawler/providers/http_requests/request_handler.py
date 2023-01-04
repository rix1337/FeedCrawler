# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
#
# Dieses Modul realisiert HTTP-Requests auf Basis der Python-eigenen urllib-Bibliothek
#
# Enthält Code von:
# https://github.com/sesh/thttp
#
# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
#
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# For more information, please refer to <https://unlicense.org>

import gzip
import json as json_lib
import ssl
from base64 import b64encode
from collections import namedtuple
from http.client import IncompleteRead
from http.cookiejar import CookieJar
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import (
    Request,
    build_opener,
    HTTPRedirectHandler,
    HTTPSHandler,
    HTTPCookieProcessor,
    ProxyHandler
)

Response = namedtuple("Response", "request content text json status_code url headers cookiejar")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request(
        url,
        params={},
        json=None,
        data=None,
        headers={},
        method="GET",
        verify=True,
        redirect=True,
        proxies={},
        cookiejar=None,
        basic_auth=None,
        timeout=None,
        output_errors=True
):
    """
    Returns a (named)tuple with the following properties:
        - request
        - content
        - text
        - json (dict; or None)
        - headers (dict; all lowercase keys)
            - https://stackoverflow.com/questions/5258977/are-http-headers-case-sensitive
        - status_code
        - url (final url, after any redirects)
        - cookiejar
    """
    method = method.upper()
    headers = {k.lower(): v for k, v in headers.items()}  # lowecase headers

    if params:
        url += "?" + urlencode(params)  # build URL from params

    url = url.replace(" ", "%20")  # replace spaces with %20

    if "@" in url and "://" in url:  # parse basic auth info from url
        split_protocol_and_url = url.split("://")

        protocol = split_protocol_and_url[0]

        split_auth_and_url = split_protocol_and_url[1].split("@")

        auth_info = split_auth_and_url[0].split(":")
        username = auth_info[0]
        password = auth_info[1]
        basic_auth = [username, password]

        url = protocol + "://" + split_auth_and_url[1]

    if json and data:
        raise Exception("Cannot provide both json and data parameters")
    if method not in ["POST", "PATCH", "PUT"] and (json or data):
        raise Exception(
            "Request method must POST, PATCH or PUT if json or data is provided"
        )
    if not timeout:
        timeout = 60

    if json:  # if we have json, stringify and put it in our data variable
        headers["content-type"] = "application/json"
        data = json_lib.dumps(json).encode("utf-8")
    elif data:
        try:
            data = urlencode(data).encode()
        except:
            data = data.encode()
    elif method in ["POST", "PATCH", "PUT"] and not data:
        data = "".encode()

    if basic_auth and len(basic_auth) == 2 and "authorization" not in headers:
        username, password = basic_auth
        headers[
            "authorization"
        ] = f'Basic {b64encode(f"{username}:{password}".encode()).decode("ascii")}'

    if not cookiejar:
        cookiejar = CookieJar()

    ctx = ssl.create_default_context()
    if not verify:  # ignore ssl errors
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    handlers = [HTTPSHandler(context=ctx), HTTPCookieProcessor(cookiejar=cookiejar)]

    if proxies:
        handlers.append(ProxyHandler(proxies=proxies))

    if not redirect:
        no_redirect = NoRedirect()
        handlers.append(no_redirect)

    opener = build_opener(*handlers)
    req = Request(url, data=data, headers=headers, method=method)

    try:
        try:
            with opener.open(req, timeout=timeout) as resp:
                status_code = resp.getcode()

                try:
                    content = resp.read()
                except IncompleteRead as er:
                    content = er.partial

                resp_url = resp.geturl()

                headers = {k.lower(): v for k, v in list(resp.info().items())}

                if "gzip" in headers.get("content-encoding", ""):
                    content = gzip.decompress(content)

                try:
                    json = (
                        json_lib.loads(content)
                        if "application/json" in headers.get("content-type", "").lower()
                           and content
                        else None
                    )
                except:
                    json = None

        except HTTPError as e:
            status_code = e.code

            try:
                content = e.read()
            except IncompleteRead as er:
                content = er.partial

            resp_url = e.geturl()

            headers = {k.lower(): v for k, v in list(e.headers.items())}

            if "gzip" in headers.get("content-encoding", ""):
                content = gzip.decompress(content)

            try:
                json = (
                    json_lib.loads(content)
                    if "application/json" in headers.get("content-type", "").lower()
                       and content
                    else None
                )
            except:
                json = None

        try:
            text = content.decode("utf-8")
        except:
            text = ""

    except Exception as e:
        if output_errors:
            print("Fehler bei Aufruf von: " + url + " (" + str(e) + ", timeout=" + str(timeout) + "s)")
        content = b""
        text = ""
        status_code = 503
        json = None
        resp_url = url

    return Response(req, content, text, json, status_code, resp_url, headers, cookiejar)
