# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt Tampermonkey-Scripte für die API des FeedCrawlers bereit.

def get_feedcrawler_helper_sj(sj, dj):
    return f"""// ==UserScript==
    // @name            FeedCrawler Helper (SJ/DJ)
    // @author          rix1337
    // @description     Forwards decrypted SJ/DJ Download links to FeedCrawler
    // @version         0.3.0
    // @require         https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js
    // @match           https://{sj}/*
    // @match           https://{dj}/*
    // @exclude         https://{sj}/serie/search?q=*
    // @exclude         https://{dj}/serie/search?q=*
    // ==/UserScript==

    document.body.addEventListener('mousedown', function (e) {{
    if (e.target.tagName != "A") return;
    var anchor = e.target;
    if (anchor.href.search(new RegExp('{sj}/serie//i')) != -1) {{
        anchor.href = anchor.href + '#' + anchor.text;
    }} else if (anchor.href.search(new RegExp('{dj}/serie//i')) != -1) {{
        anchor.href = anchor.href + '#' + anchor.text;
    }}
    }});

    var tag = window.location.hash.replace("#", "").split('|');
    var title = tag[0];
    var password = tag[1];
    if (title) {{
    $('.wrapper').prepend('<h3>[FeedCrawler Helper] ' + title + '</h3>');
    $(".container").hide();
    var checkExist = setInterval(async function () {{
        if ($("tr:contains('" + title + "')").length) {{
            $(".container").show();
            $("tr:contains('" + title + "')")[0].lastChild.firstChild.click();
            clearInterval(checkExist);
        }}
    }}, 100);
    }}"""


def get_feedcrawler_sponsors_helper_sj(sj, dj, local_address):
    return f"""// ==UserScript==
    // @name            FeedCrawler Sponsors Helper (SJ/DJ)
    // @version         0.5.2
    // @description     Clicks the correct download button on SJ/DJ sub pages to speed up Click'n'Load
    // @require         https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js
    // @match           https://{sj}/*
    // @match           https://{dj}/*
    // @exclude         https://{sj}/serie/search?q=*
    // @exclude         https://{dj}/serie/search?q=*
    // @grant           window.close
    // ==/UserScript==

    // Hier muss die von außen erreichbare Adresse des FeedCrawlers stehen (nicht bspw. die Docker-interne):
    const sponsorsURL = '{local_address}';
    // Hier kann ein Wunschhoster eingetragen werden (ohne www. und .tld):
    const sponsorsHoster = '';

    $.extend($.expr[':'], {{
        'containsi': function(elem, i, match, array) {{
            return (elem.textContent || elem.innerText || '').toLowerCase()
                .indexOf((match[3] || "").toLowerCase()) >= 0;
        }}
    }});

    document.body.addEventListener('mousedown', function (e) {{
        if (e.target.tagName != "A") return;
        var anchor = e.target;
        if (anchor.href.search(new RegExp('{sj}/serie//i')) != -1) {{
            anchor.href = anchor.href + '#' + anchor.text;
        }} else if (anchor.href.search(new RegExp('{dj}/serie//i')) != -1) {{
            anchor.href = anchor.href + '#' + anchor.text;
        }}
    }});

    const tag = window.location.hash.replace("#", "").split('|');
    const title = tag[0];
    const password = tag[1];
    if (title && title !== "login") {{
        $('.wrapper').prepend('<h3>[FeedCrawler Sponsors Helper] ' + title + '</h3>');
        $(".container").hide();
        let i = 0;
        const checkExist = setInterval(function () {{
            i++;
            if ($("tr:contains('" + title + "')").length) {{
                $(".container").show();
                $("tr:contains('" + title + "')")[0].lastChild.firstChild.click();
                if (i > 24) {{
                    const requiresLogin = $(".alert-warning").length;
                    if (requiresLogin) {{
                        console.log("[FeedCrawler Sponsors Helper] Login required for: " + title);
                        clearInterval(checkExist);
                        window.open("https://" + $(location).attr('hostname') + "#login|" + btoa(window.location));
                        window.close();
                    }}
                    clearInterval(checkExist);
                }} else {{
                    console.log("miss")
                }}
            }}
        }}, 100);

        let j = 0;
        let dl = false;
        const dlExists = setInterval(function () {{
            j++;
            if ($("tr:contains('Download Part')").length) {{
                const items = $("tr:contains('Download Part')").find("a");
                const links = [];
                items.each(function (index) {{
                    links.push(items[index].href);
                }});
                console.log("[FeedCrawler Sponsors Helper] found download links: " + links);
                clearInterval(dlExists);
                window.open(sponsorsURL + '/sponsors_helper/to_download/' + btoa(links + '|' + title + '|' + password));
                window.close();
            }} else if (j > 24 && !dl) {{
                if (sponsorsHoster && $("button:containsi('" + sponsorsHoster + "')").length) {{
                    $("button:containsi('" + sponsorsHoster + "')").click();
                }} else if ($("button:containsi('1fichier')").length) {{
                    $("button:containsi('1fichier')").click();
                }} else if ($("button:containsi('ddownload')").length) {{
                    $("button:containsi('ddownload')").click();
                }} else if ($("button:containsi('turbo')").length) {{
                    $("button:containsi('turbo')").click();
                }} else if ($("button:containsi('filer')").length) {{
                    $("button:containsi('filer')").click();
                }} else {{
                    $("div.modal-body").find("button.btn.btn-secondary.btn-block").click();
                }}
                console.log("[FeedCrawler Sponsors Helper] Clicked Download button to trigger reCAPTCHA");
                dl = true;
            }}
        }}, 100);
    }}"""


def get_feedcrawler_sponsors_helper_fc(fx, sf, local_address):
    return f"""// ==UserScript==
     // @name            FeedCrawler Sponsors Helper (FC)
     // @author          rix1337
     // @description     Forwards Click'n'Load to FeedCrawler
     // @version         0.7.4
     // @match           *.filecrypt.cc/*
     // @match           *.filecrypt.co/*
     // @match           *.filecrypt.to/*
     // @exclude         http://filecrypt.cc/helper.html*
     // @exclude         http://filecrypt.co/helper.html*
     // @exclude         http://filecrypt.to/helper.html*
     // @grant           window.close
     // ==/UserScript==

     // Hier muss die von außen erreichbare Adresse des FeedCrawlers stehen (nicht bspw. die Docker-interne):
     const sponsorsURL = '{local_address}';
     // Hier kann ein Wunschhoster eingetragen werden (ohne www. und .tld):
     const sponsorsHoster = '';

     const tag = window.location.hash.replace("#", "").split('|');
     const title = tag[0];
     const password = tag[1];
     const ids = tag[2];
     const urlParams = new URLSearchParams(window.location.search);

     function Sleep(milliseconds) {{
         return new Promise(resolve => setTimeout(resolve, milliseconds));
     }}

     let pw = "";

     let fx = false;
     try {{
         fx = (document.getElementById("customlogo").getAttribute('src') === '/css/custom/f38ed.png')
     }} catch {{}}

     const checkPass = setInterval(function () {{
         if (document.getElementById("p4assw0rt")) {{
             if (password) {{
                 pw = password;
             }} else if (fx) {{
                 pw = '{fx.split('.')[0]}';
             }} else {{
                 pw = '{sf}';
             }}
         }} else {{
             pw = "";
         }}
         clearInterval(checkPass);
     }}, 100);

     const enterPass = setInterval(function () {{
         if (pw) {{
             console.log("[FeedCrawler Sponsors Helper] entering Password: " + pw);
             try {{
                 document.getElementById("p4assw0rt").value = pw;
                 document.getElementById("p4assw0rt").parentNode.nextElementSibling.click();
             }} catch (e) {{
                 console.log("[FeedCrawler Sponsors Helper] Password set Error: " + e);
             }}
             clearInterval(enterPass);
         }}
     }}, 100);

     const checkAd = setInterval(function () {{
         if (document.querySelector('#cform > div > div > div > div > ul > li:nth-child(2)') !== null) {{
             document.querySelector('#cform > div > div > div > div > ul > li:nth-child(2)').style.display = 'none';
             clearInterval(checkAd);
         }}
     }}, 100);

     let mirrorsAvailable = false;
     try {{
         mirrorsAvailable = document.querySelector('.mirror').querySelectorAll("a");
     }} catch {{}}
     let cnlAllowed = false;

     if (mirrorsAvailable && sponsorsHoster) {{
         const currentURL = window.location.href;
         let desiredMirror = "";
         let i;
         for (i = 0; i < mirrorsAvailable.length; i++) {{
             if (mirrorsAvailable[i].text.includes(sponsorsHoster)) {{
                 let ep = "";
                 const cur_ep = urlParams.get('episode');
                 if (cur_ep) {{
                     ep = "&episode=" + cur_ep;
                 }}
                 desiredMirror = mirrorsAvailable[i].href + ep + window.location.hash;
             }}
         }}

         if (desiredMirror) {{
             if (!currentURL.toLowerCase().includes(desiredMirror.toLowerCase())) {{
                 console.log("[FeedCrawler Sponsors Helper] switching to desired Mirror: " + sponsorsHoster);
                 window.location = desiredMirror;
             }} else {{
                 console.log("[FeedCrawler Sponsors Helper] already at the desired Mirror: " + sponsorsHoster);
                 cnlAllowed = true;
             }}
         }} else {{
             console.log("[FeedCrawler Sponsors Helper] desired Mirror not available: " + sponsorsHoster);
             cnlAllowed = true;
         }}
     }} else {{
         cnlAllowed = true;
     }}

     const cnlExists = setInterval(async function () {{
         if (cnlAllowed && document.getElementsByClassName("cnlform").length) {{
             clearInterval(cnlExists);
             document.getElementById("cnl_btn").click();
             console.log("[FeedCrawler Sponsors Helper] attempting Click'n'Load");
             await Sleep(10000);
             window.close();
         }}
     }}, 100);"""


def get_feedcrawler_sponsors_helper_nx(nx, local_address):
    return f"""// ==UserScript==
    // @name            FeedCrawler Sponsors Helper (NX)
    // @author          rix1337
    // @description     Forwards decrypted links to FeedCrawler
    // @version         0.1.1
    // @require         https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js
    // @match           https://{nx}/release/*
    // @grant           window.close
    // ==/UserScript==
    // Hier muss die von außen erreichbare Adresse des FeedCrawlers stehen (nicht bspw. die Docker-interne):
    const sponsorsURL = '{local_address}';

    function Sleep(milliseconds) {{
        return new Promise(resolve => setTimeout(resolve, milliseconds));
    }}

    var tag = window.location.hash.replace("#", "").split('|');
    var title = tag[0];
    var password = '{nx}';

    if (title) {{
        await Sleep(3000);
        $('h2').prepend('<h3>[FeedCrawler Sponsors Helper] ' + title + '</h3>');
        var dl = false;
        var dlExists = setInterval(function() {{
            console.log($("tr:contains("+ title +")").find("a[href*=filer]").length)
            if ($("tr:contains("+ title +")").find("a[href*=filer]").length) {{
                var link = $("tr:contains("+ title +")").find("a[href*=filer]")[0]["href"].replace("https://referer.to/?", "");
                var links = [link];
                console.log("[FeedCrawler Sponsors Helper] found download links: " + links);
                clearInterval(dlExists);
                window.open(sponsorsURL + '/sponsors_helper/to_download/' + btoa(links + '|' + title + '|' + password));
                window.close();
            }}
        }}, 1000);
        var tolinkExists = setInterval(function() {{
            console.log($("tr:contains("+ title +")").find("a[href*=tolink]").length)
            if ($("tr:contains("+ title +")").find("a[href*=tolink]").length) {{
                var link = $("tr:contains("+ title +")").find("a[href*=tolink]")[0]["href"].replace("https://referer.to/?", "");
                var links = [link];
                console.log("[FeedCrawler Sponsors Helper] found encrypted download links: " + links);
                clearInterval(tolinkExists);
                window.open(sponsorsURL + '/sponsors_helper/replace_decrypt/' + btoa(links + '|' + title + '|' + password));
                window.close();
            }}
        }}, 1000);
    }}"""
