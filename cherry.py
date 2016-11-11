# -*- coding: utf-8 -*-
# RSScrawler - Version 2.2.7
# Projekt von https://github.com/rix1337
# Enthält Code von:
# http://codepen.io/colorlib/pen/KVoZyv
# http://codepen.io/cbracco/pen/qzukg
# https://github.com/jaysonwm/popupmodal.js

import cherrypy
import os, sys
import StringIO
from rssconfig import RssConfig
import common
import files

# Globale Variable
version = "v.2.2.7"

class Server:
  # Zeige Konfigurationsseite
  @cherrypy.expose
  def index(self):
    jdownloader, port, prefix, interval, hoster, pushbulletapi, mbquality, ignore, historical, mbregex, cutoff, crawl3d, enforcedl, crawlseasons, seasonsquality, seasonssource, sjquality, rejectlist, sjregex, hosterso, hosterul, mbq1080, mbq720, mbq480, msq1080, msq720, msq480, sjq1080, sjq720, sjq480, historicaltrue, historicalfalse, mbregextrue, mbregexfalse, mrdiv, cutofftrue, cutofffalse, crawl3dtrue, crawl3dfalse, tddiv, enforcedltrue, enforcedlfalse, crawlseasonstrue, crawlseasonsfalse, ssdiv, sjregextrue, sjregexfalse, srdiv, dockerblocker, dockerhint = common.load(dockerglobal)
    return '''<!DOCTYPE html>
<html lang="de">
  <head>
    <meta charset="utf-8">
    <meta content="width=device-width,maximum-scale=1" name="viewport">
    <meta content="noindex, nofollow" name="robots">
    <title>RSScrawler</title>
    <link href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQBAMAAADt3eJSAAAABGdBTUEAALGPC/xhBQAAAAFzUkdCAK7OHOkAAAAJcEhZcwAACxMAAAsTAQCanBgAAAAwUExURUxpcQEBAQMDAwAAAAAAAAICAgAAAAAAAAAAAAEBAQQEBAEBAQMDAwEBAQICAgAAAHF9S8wAAAAPdFJOUwBkHuP2K8qzcEYVmzhVineWhWQAAAB4SURBVAjXY2CAAaabChAG4xdzIQjj//9vAiAGZ7L/f+8FINai2fb/q4A0z1uF4/9/g9XYae3/IgBWnLr8fxIDA2u7/zcd+x9AuTXC/x/s/76AgSml0N90yucABt7/nvUfF3+ZwMBqn9T/j+0/UNvBgIhO3o4AuCsAPDssr9goPWoAAABXelRYdFJhdyBwcm9maWxlIHR5cGUgaXB0YwAAeJzj8gwIcVYoKMpPy8xJ5VIAAyMLLmMLEyMTS5MUAxMgRIA0w2QDI7NUIMvY1MjEzMQcxAfLgEigSi4A6hcRdPJCNZUAAAAASUVORK5CYII=" rel="icon" type="image/png">
    <style>
      @import url(https://fonts.googleapis.com/css?family=Roboto:400,300,600,400italic);body,h1{font-family:Roboto,Helvetica,Arial,sans-serif;line-height:30px}.popup_modals .modal_buttons .btn:hover,[hinweis]{cursor:pointer}h1{font-weight:300;font-size:30px}.copyright,[hinweis]:before,div,h1,h2,h3,input{text-align:center}*{margin:0;padding:0;box-sizing:border-box;-webkit-box-sizing:border-box;-moz-box-sizing:border-box;-webkit-font-smoothing:antialiased;-moz-font-smoothing:antialiased;-o-font-smoothing:antialiased;font-smoothing:antialiased;text-rendering:optimizeLegibility}body{font-weight:100;font-size:14px;color:#000;background:#d3d3d3}#rsscrawler button,#rsscrawler iframe,#rsscrawler input[type=text],#rsscrawler select,#rsscrawler textarea,.popup_modals .modal_buttons .btn.btn_pmry{font:400 12px/16px Roboto,Helvetica,Arial,sans-serif}.container{max-width:800px;width:100%;margin:0 auto;position:relative}[hinweis]:after,[hinweis]:before{position:absolute;bottom:150%;left:50%;visibility:hidden;-ms-filter:"progid:DXImageTransform.Microsoft.Alpha(Opacity=0)";filter:progid: DXImageTransform.Microsoft.Alpha(Opacity=0);opacity:0;pointer-events:none}#rsscrawler{background:#F9F9F9;padding:25px;margin:50px 0;box-shadow:0 0 20px 0 rgba(0,0,0,.2),0 5px 5px 0 rgba(0,0,0,.24)}#rsscrawler h1{display:block;font-size:30px;font-weight:300;margin-bottom:10px}#rsscrawler h4{margin:5px 0 15px;display:block;font-size:13px;font-weight:400}fieldset{border:none!important;margin:0 0 10px;min-width:100%;padding:0;width:100%}#rsscrawler iframe,#rsscrawler input[type=text],#rsscrawler select,#rsscrawler textarea{width:100%;border:1px solid #ccc;background:#FFF;margin:0 0 5px;padding:10px}#rsscrawler iframe,#rsscrawler input[type=text]:hover,#rsscrawler select,#rsscrawler textarea:hover{-webkit-transition:border-color .3s ease-in-out;-moz-transition:border-color .3s ease-in-out;transition:border-color .3s ease-in-out;border:1px solid #aaa}#rsscrawler button:hover,.popup_modals .modal_buttons .btn.btn_pmry:hover{-webkit-transition:background .3s ease-in-out;-moz-transition:background .3s ease-in-out}#rsscrawler select{padding-left:24px;text-align:center;text-align-last:center}#rsscrawler textarea{height:100px;max-width:100%;resize:none}#rsscrawler button{cursor:pointer;width:100%;border:none;background:#333;color:#FFF;margin:0 0 5px;padding:10px;font-size:15px}#rsscrawler button:hover{background:#43A047;transition:background-color .3s ease-in-out}#rsscrawler button:active{box-shadow:inset 0 1px 3px rgba(0,0,0,.5)}#rsscrawler input:focus,#rsscrawler textarea:focus{outline:0;border:1px solid #aaa}::-webkit-input-placeholder{color:#888}:-moz-placeholder{color:#888}::-moz-placeholder{color:#888}:-ms-input-placeholder{color:#888}[hinweis]{position:relative;z-index:2}[hinweis]:before{margin-bottom:5px;margin-left:-400px;padding:9px;width:782px;-webkit-border-radius:3px;-moz-border-radius:3px;border-radius:0;background-color:#000;background-color:hsla(0,0%,20%,.9);color:#fff;content:attr(hinweis);font-size:14px;line-height:1.2}[hinweis]:after{margin-left:-5px;width:0;border-top:5px solid #000;border-top:5px solid hsla(0,0%,20%,.9);border-right:5px solid transparent;border-left:5px solid transparent;content:" ";font-size:0;line-height:0}[hinweis]:hover:after,[hinweis]:hover:before{visibility:visible;-ms-filter:"progid:DXImageTransform.Microsoft.Alpha(Opacity=100)";filter:progid: DXImageTransform.Microsoft.Alpha(Opacity=100);opacity:1}.modal_backdrop,.popup_modals{color:#000;position:fixed;box-shadow:0 0 20px 0 rgba(0,0,0,.2),0 5px 5px 0 rgba(0,0,0,.24);top:0;right:0;left:0}.popup_modals{margin:5% auto;border-radius:0;background-color:#f5f5f5;color:#000;-webkit-transition:opacity .15s,-webkit-transform .3s;transition:opacity .15s,-webkit-transform .3s;transition:opacity .15s,transform .3s;transition:opacity .15s,transform .3s,-webkit-transform .3s}.popup_modals.modal_small{width:400px}.popup_modals.modal_medium{width:500px}.popup_modals.modal_large{width:600px}.popup_modals.fade{opacity:0;filter:alpha(opacity=0)}.popup_modals.top{-webkit-transform:translate(0,-25%);-ms-transform:translate(0,-25%);transform:translate(0,-25%)}.popup_modals.bottom{-webkit-transform:translate(0,25%);-ms-transform:translate(0,25%);transform:translate(0,25%)}.popup_modals.right{-webkit-transform:translate(25%,0);-ms-transform:translate(25%,0);transform:translate(25%,0)}.popup_modals.left{-webkit-transform:translate(-25%,0);-ms-transform:translate(-25%,0);transform:translate(-25%,0)}.popup_modals.in{opacity:1;filter:alpha(opacity=100);-webkit-transform:translate(0,0);-ms-transform:translate(0,0);transform:translate(0,0)}.popup_modals .modal_content{padding:20px}.popup_modals .modal_content .modal_input{margin-top:10px;padding:7px 10px;border-radius:4px;border:1px solid #d2dee2;box-sizing:border-box}.popup_modals .modal_buttons{padding:10px;text-transform:uppercase;letter-spacing:1px}.popup_modals .modal_buttons.right{text-align:right}.popup_modals .modal_buttons.right .btn{margin-left:5px}.popup_modals .modal_buttons.left{text-align:center}.popup_modals .modal_buttons.left .btn{margin-right:5px}.popup_modals .modal_buttons .btn{display:inline-block;color:#fff;text-decoration:none;padding:7px 10px;border-radius:0;font-size:14px}.popup_modals .modal_buttons .btn.btn_pmry{cursor:pointer;width:100%;border:none;background:#333;color:#FFF;margin:0 0 5px;padding:10px;font-size:15px}.popup_modals .modal_buttons .btn.btn_pmry:hover{background:#43A047;transition:background-color .3s ease-in-out}.popup_modals .modal_buttons .btn.btn_pmry:active{box-shadow:inset 0 1px 3px rgba(0,0,0,.5)}.popup_modals .modal_buttons .btn.btn_sdry{font:400 12px/16px Roboto,Helvetica,Arial,sans-serif;cursor:pointer;width:100%;border:none;background:#333;color:#FFF;margin:0 0 5px;padding:10px;font-size:15px}.popup_modals .modal_buttons .btn.btn_sdry:hover{background:#e74c3c;-webkit-transition:background .3s ease-in-out;-moz-transition:background .3s ease-in-out;transition:background-color .3s ease-in-out}.popup_modals .modal_buttons .btn.btn_extra{background-color:#7f8c8d}.modal_backdrop{bottom:0;-webkit-transition:all .15s;transition:all .15s}.modal_backdrop.fade{opacity:0;filter:alpha(opacity=0)}
    </style>
    <script>
      function getBrowserName(){var a="Unknown";return navigator.userAgent.indexOf("MSIE")!=-1?a="MSIE":navigator.userAgent.indexOf("Edge")!=-1?a="Edge":navigator.userAgent.indexOf("Firefox")!=-1?a="Firefox":navigator.userAgent.indexOf("Opera")!=-1?a="Opera":navigator.userAgent.indexOf("Chrome")!=-1?a="Chrome":navigator.userAgent.indexOf("Safari")!=-1&&(a="Safari"),a}"Unknown"==getBrowserName()?document.location.href="''' + prefix + '''/legacy":"MSIE"==getBrowserName()?document.location.href="''' + prefix + '''/legacy":"Edge"==getBrowserName()?document.location.href="''' + prefix + '''/legacy":"Safari"==getBrowserName()&&(document.location.href="''' + prefix + '''/legacy");
    </script>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.12.4/jquery.min.js"></script>
    <script>
      $(document).ready(function(){$("#smbr").on("change",function(){"True"==this.value?$("#dmbr").show():$("#dmbr").hide()}),$("#smb3").on("change",function(){"True"==this.value?$("#dmb3").show():$("#dmb3").hide()}),$("#smbs").on("change",function(){"True"==this.value?($("#dmbss").show(),$("#dmbs").show()):($("#dmbss").hide(),$("#dmbs").hide())}),$("#ssjr").on("change",function(){"True"==this.value?$("#dsjr").show():$("#dsjr").hide()})});
    </script>
    </script>
    <script>
      "use strict";function _typeof(e){return e&&"undefined"!=typeof Symbol&&e.constructor===Symbol?"symbol":typeof e}var popup;!function(){var e=0,t=[],o=[],n=!0,l=!0,d="left",a="small",c="#000",r="top",i=void 0,m="modal_backdrop",s={},u=function(t){1==t?++e:--e,i="popup_modal_"+e},p=function(){u(!0);var t=document.createElement("div");t.id="popup_modal_"+e,t.className="popup_modals fade "+o[o.length-1].modal_effect;var n=o[o.length-1].modal_size;"string"==typeof n?t.className+=" modal_"+o[o.length-1].modal_size:"number"==typeof n&&(t.style.width=n+"px");var l=document.createElement("div");l.className="modal_content";var d=document.createElement("div");d.className="modal_buttons "+o[o.length-1].btn_align,t.appendChild(l),t.appendChild(d),document.body.appendChild(t)},f=function(e,t){var o=!0,n=!1,l=void 0;try{for(var d,a=e[Symbol.iterator]();!(o=(d=a.next()).done);o=!0){var c=d.value;if(c==t)return!0}}catch(r){n=!0,l=r}finally{try{!o&&a["return"]&&a["return"]()}finally{if(n)throw l}}return!1},y=function(e,t){e.className+=" "+t},_=function(e,t){var o=new RegExp("(?:^|\\s)"+t+"(?!\\S)","g");e.className=e.className.replace(o,"")},b=function(e){var o=t[t.length-1],n={e:e,proceed:!1};if("click"==e.type?f(e.currentTarget.classList,"btn_pmry")?(n.proceed=!0,console.log("Click proceed : true")):console.log("Click proceed : false"):"keydown"==e.type&&(13==e.keyCode?(n.proceed=!0,console.log("Keydown proceed : true")):console.log("Keydown proceed : false")),o){var l=document.getElementById(i).getElementsByClassName("modal_input")[0];n.input_value=l?l.value:null,setTimeout(function(){o(n)},350)}I()},g=function(t){for(var o in s)if("alert"!=t||1!=Object.keys(s).indexOf(o)){var n=s[o],l=void 0,d=document.createElement("a");d.id=l=n.btn_id+"_"+e,d.className=n.btn_class,d.innerHTML=n.inner_text,document.getElementById(i).getElementsByClassName("modal_buttons")[0].appendChild(d),document.getElementById(l).addEventListener("click",function(e){b(e)})}},v=function(e){(13==e.keyCode||27==e.keyCode)&&b(e)},h=function(e){b(e)},E=function(){document.getElementById("modal_backdrop").removeEventListener("click",h),o[o.length-1].backdrop_close&&document.getElementById(m).addEventListener("click",h)},k=function(){document.removeEventListener("keydown",v),o[o.length-1].keyboard&&document.addEventListener("keydown",v)},B=function(){var t=document.createElement("div");if(t.id=m,t.className="modal_backdrop fade",document.getElementById(i).style.zIndex=5+10*e,2>e)document.body.appendChild(t);else{for(var n=e-1;n>0;n--)document.getElementById("popup_modal_"+n).style.transform="translate(-"+20*(e-n)+"px, -"+20*(e-n)+"px)";document.getElementById(m).style.zIndex=10*e,console.log("popup_modal_"+(e-1)+" : hidden")}document.getElementById(m).style.background=o[o.length-1].bg_overlay_color,setTimeout(function(){2>e&&y(document.getElementById(m),"in"),setTimeout(function(){y(document.getElementById(i),"in"),console.log(i+" : shown");var e=document.getElementById(i).getElementsByClassName("modal_input")[0];e&&e.focus(),E(),k()},150)},150)},I=function(){document.removeEventListener("keydown",v),document.getElementById("modal_backdrop").removeEventListener("click",h),_(document.getElementById(i),"in"),console.log(i+" : hidden"),setTimeout(function(){2>e&&_(document.getElementById(m),"in"),setTimeout(function(){if(document.body.removeChild(document.getElementById(i)),u(!1),o.pop(),t.pop(),1>e)document.body.removeChild(document.getElementById(m));else{document.getElementById(m).style.background=o[o.length-1].bg_overlay_color,document.getElementById(m).style.zIndex=10*e;for(var n=e;n>0;n--)document.getElementById("popup_modal_"+n).style.transform="translate(-"+20*(e-n)+"px, -"+20*(e-n)+"px)",n==e&&(document.getElementById(i).style.removeProperty?document.getElementById(i).style.removeProperty("transform"):document.getElementById(i).style.removeAttribute("transform"));console.log("popup_modal_"+e+" : shown");var l=document.getElementById("popup_modal_"+e).getElementsByClassName("modal_input")[0];l&&l.focus(),E(),k()}},150)},150)},w=function(e,m,u){var f=99,y="",_=document.createElement("div"),b=void 0,v=void 0,h={};try{if(!m||"object"!==("undefined"==typeof m?"undefined":_typeof(m)))throw"No content specified.";if(!m.content)throw"content not specified";if(_.innerHTML=m.content,void 0!==m.keyboard){if("boolean"!=typeof m.keyboard)throw"keyboard is not type boolean";h.keyboard=m.keyboard}else h.keyboard=n;if(void 0!==m.backdrop_close){if("boolean"!=typeof m.backdrop_close)throw"backdrop_close is not type boolean";h.backdrop_close=m.backdrop_close}else h.backdrop_close=l;if(m.placeholder){if("string"!=typeof m.placeholder)throw"placeholder is not type string";y=m.placeholder}if(m.input_length){if("number"!=typeof m.input_length)throw"input_length is not type number";f=m.input_length}if(m.default_btns){if("object"!==_typeof(m.default_btns))throw"default_btns is not type object";var E=m.default_btns;b=E.ok,v=E.cancel}if(s={ok:{btn_id:"btn_ok",btn_class:"btn btn_pmry",inner_text:b||"Ok"},cancel:{btn_id:"btn_cancel",btn_class:"btn btn_sdry",inner_text:v||"Cancel"}},m.custom_btns){if("object"!==_typeof(m.custom_btns))throw"custom_btns is not type object";var k=0;for(var I in m.custom_btns)s[I]={btn_id:"btn_extra_"+ ++k,btn_class:"btn btn_extra",inner_text:m.custom_btns[I]}}if(m.btn_align&&"left"!==m.btn_align&&"right"!==m.btn_align)throw'btn_align is not type string and only accepts value of "left" or "right"';if(h.btn_align=m.btn_align||d,m.modal_size&&"number"!=typeof m.modal_size&&"large"!==m.modal_size&&"medium"!==m.modal_size&&"small"!==m.modal_size)throw'modal_size is not type number / string and only accepts value of "small", "medium" or "large"';if(h.modal_size=m.modal_size||a,m.bg_overlay_color&&"string"!=typeof m.bg_overlay_color)throw"bg_overlay_color is not type string";if(h.bg_overlay_color=m.bg_overlay_color||c,m.effect&&"top"!==m.effect&&"bottom"!==m.effect&&"right"!==m.effect&&"left"!==m.effect&&"none"!==m.effect)throw'effect is not type string and onlty accepts value of "top", "bottom", "right", "left" or "none"';h.modal_effect=m.effect||r}catch(w){return void console.warn(w+". Rollback.")}if(o.push(h),u?t.push(u):t.push(null),p(),g(e),document.getElementById(i).getElementsByClassName("modal_content")[0].appendChild(_),"prompt"==e){var C=document.createElement("input");C.type="text",C.className="modal_input",C.placeholder=y,C.maxLength=f,C.style.width="100%",document.getElementById(i).getElementsByClassName("modal_content")[0].appendChild(C)}B()},C=function(e,t){w("alert",e,t)},x=function(e,t){w("confirm",e,t)},N=function(e,t){w("prompt",e,t)};popup={alert:C,prompt:N,confirm:x}}();
    </script>
  </head>
  <body>
  <div class="container">
    <form id="rsscrawler" action="https://github.com/rix1337/thanks" target="_blank">
          <img src="data:image/png;base64,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" alt=""/>
          <h1>RSScrawler</h1>
          ''' + version + ''' (Projekt von <a href="https://github.com/rix1337/RSScrawler/commits" target="_blank">RiX</a>)
          <button type="submit">Bedanken</button>
    </form>
    <form id="rsscrawler" name="log" enctype="multipart/form-data" target="speichernFrame" method="post" action="logleeren?wert=1">
          <h1>Log</h1>
            <iframe sandbox="allow-forms allow-same-origin allow-pointer-lock allow-scripts allow-popups allow-modals" src="./log" width="800" height="240">
            Dieser Browser unterstützt keine iFrames. Stattdessen <a href = "/log">/log</a> aufrufen.
          </iframe>
          <button type="button" onclick="popup.confirm({content:'<h1>Log leeren?</h1>',default_btns:{cancel:'Abbrechen'}},function(a){a.proceed&&(document.forms.log.submit(),popup.alert({content:'<h1>Log geleert</h1>'},function(a){a.proceed&&window.location.reload()}))});">Leeren</button>
    </form>
    <form id="rsscrawler" enctype="multipart/form-data" target="speichernFrame" method="post" action="listenspeichern">
          <h1>Suchlisten</h1>
          <div hinweis="Dieser Bereich ist für die Suche auf ''' + "TW92aWUtQmxvZw==".decode('base64') + ''' zuständig."><h3>''' + "TW92aWUtQmxvZw==".decode('base64') + '''</h3></div>
          <div hinweis="Pro Zeile ein Filmtitel (wahlweise mit Erscheinungsjahr).">Filme</div>
          <textarea name="mbfilme">''' + self.getListe('MB_Filme') + '''</textarea>
          <div style='display:''' + tddiv +''';' id='dmb3'><div hinweis="Pro Zeile ein Filmtitel (wahlweise mit Erscheinungsjahr).">3D-Filme</div>
          <textarea name="mb3d">''' + self.getListe('MB_3D') + '''</textarea></div>
          <div style='display:''' + ssdiv +''';' id='dmbs'><div hinweis="Pro Zeile ein Serientitel für ganze Staffeln.">Staffeln</div>
          <textarea name="mbstaffeln">''' + self.getListe('MB_Staffeln') + '''</textarea></div>
          <div style='display:''' + mrdiv +''';' id='dmbr'><div hinweis="Pro Zeile ein Film-/Serientitel im RegEx-Format. Die Filterliste wird hierbei ignoriert!">Filme/Serien (RegEx)</div>
          <textarea name="mbregex">''' + self.getListe('MB_Regex') + '''</textarea></div>
          <div hinweis="Dieser Bereich ist für die Suche auf ''' + "U2VyaWVuSnVua2llcw==".decode('base64') + ''' zuständig."><h3>''' + "U2VyaWVuSnVua2llcw==".decode('base64') + '''</h3></div>
          <div hinweis="Pro Zeile ein Serientitel.">Serien</div>
          <textarea name="sjserien">''' + self.getListe('SJ_Serien') + '''</textarea>
          <div style='display:''' + srdiv +''';' id='dsjr'><div hinweis="Pro Zeile ein Serientitel im RegEx-Format. Die Filterliste wird hierbei ignoriert!">Serien (RegEx)</div>
          <textarea name="sjregex">''' + self.getListe('SJ_Serien_Regex') + '''</textarea></div>
          <button type="submit" onclick="popup.alert({content:'<h1>Listen gespeichert</h1><br />Um sofort nach neuen Titeln zu suchen, muss neu gestartet werden.'},function(a){a.proceed&&window.location.reload()});">Speichern</button>
    </form>
    <form id="rsscrawler" action="https://www.9kw.eu/register_87296.html" target="_blank">
          <h1>Hilfe</h1>
          <div id="regex-hinweise"  style="display:none;"><h1>Hilfe zu Regex</h1><h3>Beispiele für ''' + "TW92aWUtQmxvZw==".decode('base64') + '''</h3><i>Film.*.Titel.*</i><br />Sucht nach allen Filmen die mit Film beginnen und Titel enthalten.<br /><i>.*-GROUP</i> oder <i>-GROUP</i><br />sucht nach allen Releases der GROUP.<br /><i>.*1080p.*-GROUP</i><br />sucht nach allen Full-HD Releases der GROUP.<br /><i>Film.Titel.*.DL.*.720p.*.BluRay.*-Group</i><br/>sucht nach HD-BluRay Releases von Film Titel, zweisprachig und in 720p der GROUP.<h3>Beispiele für ''' + "U2VyaWVuSnVua2llcw==".decode('base64') + '''</h3><i>DEUTSCH.*Serien.Titel.*.S01.*.720p.*-GROUP</i><br />sucht nach Releases der GROUP von Staffel 1 der Serien Titel in 720p auf Deutsch.<br /><i>Serien.Titel.*</i><br />sucht nach allen Releases von Serien Titel (nützlich, wenn man sonst HDTV aussortiert).<br /><i>Serien.Titel.*.DL.*.720p.*</i><br />sucht nach zweisprachigen Releases in 720p von Serien Titel.<br /><i>ENGLISCH.*Serien.Titel.*.1080p.*</i><br />sucht nach englischen Releases in Full-HD von Serien Titel.<br /><i>(?!(Diese|Andere)).*Serie.*.DL.*.720p.*-(GROUP|ANDEREGROUP)</i><br />sucht nach Serie (aber nicht Diese Serie oder Andere Serie), zweisprachig und in 720p und ausschließlich nach Releases von GROUP oder ANDEREGROUP.<h3>All diese Regeln lassen sich beliebig kombinieren.</h3>Falsche Regex-Einträge können allerdings das Script zum Absturz bringen!</div>
          <button id="regex-hinweisbutton"type="button" onclick="document.getElementById('regex-hinweise').style.display='block';document.getElementById('regex-hinweisbutton').style.display='none';">Hilfe zu Regex</button>
          <button type="submit">Captchas automatisch lösen</button>
    </form>
    <form id="rsscrawler" enctype="multipart/form-data" target="speichernFrame" method="post" action="speichern">
          <div hinweis="Hier werden sämtliche Einstellungen von RSScrawler hinterlegt. Dieses Script funktioniert nur sinnvoll, wenn Ordnerüberwachung im JDownloader aktiviert ist. Es muss weiterhin unten der richtige JDownloader Pfad gesetzt werden!">
          <h1>Einstellungen</h1></div>
          <div hinweis="Diese allgemeinen Einstellungen müssen korrekt sein!"><h3>Allgemein</h3></div>
          Pfad des JDownloaders:<div hinweis="''' + dockerhint +'''Dieser Pfad muss das exakte Verzeichnis des JDownloaders sein, sonst funktioniert das Script nicht!"><input type="text" value="''' + jdownloader +'''" name="jdownloader"''' + dockerblocker +'''></div>
          Port:<div hinweis="''' + dockerhint +'''Hier den Port des Webservers wählen."><input type="text" name="port" value="''' + port +'''"''' + dockerblocker +'''></div>
          Prefix:<div hinweis="Hier den Prefix des Webservers wählen (nützlich für Reverse-Proxies)."><input type="text" name="prefix" value="''' + prefix.replace("/", "") +'''"></div>
          Suchintervall:<div hinweis="Das Suchintervall in Minuten sollte nicht zu niedrig angesetzt werden, um keinen Ban zu riskieren. Minimum sind 3 Minuten!"><input type="text" name="interval" value="''' + interval +'''"></div>
          Pushbullet Token:<div hinweis="Um über hinzugefügte Releases informiert zu werden, hier den Pushbullet API-Token eintragen."><input type="text" name="pushbulletapi" value="''' + pushbulletapi +'''"></div>
          Hoster:<div hinweis="Hier den gewünschten Hoster wählen."><select name="hoster"><option value="Uploaded"''' + hosterul + '''>Uploaded.net</option><option value="Share-Online"''' + hosterso + '''>Share-Online.biz</option></select></div>
          <div hinweis="Dieser Bereich ist für die Suche auf ''' + "TW92aWUtQmxvZw==".decode('base64') + ''' zuständig."><h3>''' + "TW92aWUtQmxvZw==".decode('base64') + '''</h3></div>
          Auflösung:<div hinweis="Die Release-Auflösung, nach der gesucht wird."><select name="mbquality"><option value="1080p"''' + mbq1080 + '''>Full-HD</option><option value="720p"''' + mbq720 + '''>HD</option><option value="480p"''' + mbq480 + '''>SD</option></select></div>
          Filterliste:<div hinweis="Releases mit diesen Begriffen werden nicht hinzugefügt (durch Kommata getrennt)."><input type="text" name="ignore" value="''' + ignore +'''"></div>
          Suchfunktion, statt Feed nutzen:<div hinweis="Wenn aktiviert, wird die Suchfunktion des ''' + "TW92aWUtQmxvZw==".decode('base64') + ''' genutzt, da der Feed nur wenige Stunden abbildet."><select name="historical"><option value="True"''' + historicaltrue + '''>Aktiviert</option><option value="False"''' + historicalfalse + '''>Deaktiviert</option></select></div>
          Zweisprachige Releases suchen:<div hinweis="Wenn aktiviert, sucht das Script zu jedem nicht zweisprachigen Release (kein DL-Tag im Titel) ein passendes Release in 1080p mit DL Tag. Findet das Script kein Release wird dies im DEBUG-Log vermerkt. Bei der nächsten Ausführung versucht das Script dann erneut ein passendes Release zu finden. Diese Funktion ist nützlich um (durch späteres Remuxen) eine zweisprachige Bibliothek in 720p zu erhalten."><select name="enforcedl"><option value="True"''' + enforcedltrue + '''>Aktiviert</option><option value="False"''' + enforcedlfalse + '''>Deaktiviert</option></select></div>
          Filmtitel nach Retail entfernen:<div hinweis="Wenn aktiviert, werden Filme aus der Filme-Liste gestrichen, sobald ein Retail-Release gefunden wurde."><select name="cutoff"><option value="True"''' + cutofftrue + '''>Aktiviert</option><option value="False"''' + cutofffalse + '''>Deaktiviert</option></select></div>
          3D-Releases suchen:<div hinweis="Wenn aktiviert, sucht das Script zusätzlich auch nach 3D Releases (in 1080p), unabhängig von der oben gesetzten Auflösung."><select id="smb3" name="crawl3d"><option value="True"''' + crawl3dtrue + '''>Aktiviert</option><option value="False"''' + crawl3dfalse + '''>Deaktiviert</option></select></div>
          Staffeln suchen:<div hinweis="Wenn aktiviert, werden komplette Staffeln entsprechend der Staffel-Liste auf ''' + "TW92aWUtQmxvZw==".decode('base64') + ''' gesucht."><select id="smbs" name="crawlseasons"><option value="True"''' + crawlseasonstrue + '''>Aktiviert</option><option value="False"''' + crawlseasonsfalse + '''>Deaktiviert</option></select></div>
          <div style='display:''' + ssdiv +''';' id='dmbss'>Auflösung der Staffeln:<div hinweis="Die Release-Auflösung der Staffeln, nach der gesucht wird."><select name="seasonsquality"><option value="1080p"''' + msq1080 + '''>Full-HD</option><option value="720p"''' + msq720 + '''>HD</option><option value="480p"''' + msq480 + '''>SD</option></select></div>
          Quellart der Staffeln:<div hinweis="Die Quellart der Staffeln, nach der gesucht wird (BluRay, WEB, HDTV, ...)."><input type="text" name="seasonssource" value="''' + seasonssource +'''"></div></div>
          Auch per RegEx-Funktion suchen:<div hinweis="Wenn aktiviert, werden Filme aus der Filme (RegEx)-Liste nach den entsprechenden Regeln gesucht."><select id="smbr" name="mbregex"><option value="True"''' + mbregextrue + '''>Aktiviert</option><option value="False"''' + mbregexfalse + '''>Deaktiviert</option></select></div>
          <div hinweis="Dieser Bereich ist für die Suche auf ''' + "U2VyaWVuSnVua2llcw==".decode('base64') + ''' zuständig."><h3>''' + "U2VyaWVuSnVua2llcw==".decode('base64') + '''</h3></div>
          <p>Auflösung:<div hinweis="Die Release-Auflösung, nach der gesucht wird."><select name="sjquality"><option value="1080p"''' + sjq1080 + '''>Full-HD</option><option value="720p"''' + sjq720 + '''>HD</option><option value="480p"''' + sjq480 + '''>SD</option></select></div>
          Filterliste:<div hinweis="Releases mit diesen Begriffen werden nicht hinzugefügt (durch Kommata getrennt)."><input type="text" name="rejectlist" value="''' + rejectlist +'''"></div>
          Auch per RegEx-Funktion suchen:<div hinweis="Wenn aktiviert, werden Serien aus der Serien (RegEx)-Liste nach den entsprechenden Regeln gesucht."><select id="ssjr" name="sjregex"><option value="True"''' + sjregextrue + '''>Aktiviert</option><option value="False"''' + sjregexfalse + '''>Deaktiviert</option></select></div>
          <button type="submit" onclick="popup.alert({content:'<h1>Einstellungen gespeichert</h1><br />Um einige Änderungen anzunehmen, muss neu gestartet werden.'},function(a){a.proceed&&window.location.reload()});">Speichern</button>
    </form>
    <form id="rsscrawler" name="neustart" enctype="multipart/form-data" target="speichernFrame" method="post" action="neustart?wert=1">
          <button type="button" onclick="popup.confirm({content:'<h1>Neu starten?</h1>',default_btns:{cancel:'Abbrechen'}},function(a){a.proceed&&(document.forms.neustart.submit(),popup.alert({content:'<h1>Neu gestartet</h1>'},function(a){a.proceed&&window.location.reload()}))});">Neu starten</button>
    </form>
  </div>
  <iframe name="speichernFrame" width="0" height="0" style="display: none;"></iframe>
  </body>
</html>'''

  @cherrypy.expose
  def legacy(self):
    jdownloader, port, prefix, interval, hoster, pushbulletapi, mbquality, ignore, historical, mbregex, cutoff, crawl3d, enforcedl, crawlseasons, seasonsquality, seasonssource, sjquality, rejectlist, sjregex, hosterso, hosterul, mbq1080, mbq720, mbq480, msq1080, msq720, msq480, sjq1080, sjq720, sjq480, historicaltrue, historicalfalse, mbregextrue, mbregexfalse, mrdiv, cutofftrue, cutofffalse, crawl3dtrue, crawl3dfalse, tddiv, enforcedltrue, enforcedlfalse, crawlseasonstrue, crawlseasonsfalse, ssdiv, sjregextrue, sjregexfalse, srdiv, dockerblocker, dockerhint = common.load(dockerglobal)
    return '''<!DOCTYPE html>
<html lang="de">
  <head>
    <meta charset="utf-8">
    <meta content="width=device-width,maximum-scale=1" name="viewport">
    <meta content="noindex, nofollow" name="robots">
    <title>RSScrawler</title>
    <link href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQBAMAAADt3eJSAAAABGdBTUEAALGPC/xhBQAAAAFzUkdCAK7OHOkAAAAJcEhZcwAACxMAAAsTAQCanBgAAAAwUExURUxpcQEBAQMDAwAAAAAAAAICAgAAAAAAAAAAAAEBAQQEBAEBAQMDAwEBAQICAgAAAHF9S8wAAAAPdFJOUwBkHuP2K8qzcEYVmzhVineWhWQAAAB4SURBVAjXY2CAAaabChAG4xdzIQjj//9vAiAGZ7L/f+8FINai2fb/q4A0z1uF4/9/g9XYae3/IgBWnLr8fxIDA2u7/zcd+x9AuTXC/x/s/76AgSml0N90yucABt7/nvUfF3+ZwMBqn9T/j+0/UNvBgIhO3o4AuCsAPDssr9goPWoAAABXelRYdFJhdyBwcm9maWxlIHR5cGUgaXB0YwAAeJzj8gwIcVYoKMpPy8xJ5VIAAyMLLmMLEyMTS5MUAxMgRIA0w2QDI7NUIMvY1MjEzMQcxAfLgEigSi4A6hcRdPJCNZUAAAAASUVORK5CYII=" rel="icon" type="image/png">
    <style>
      @import url(https://fonts.googleapis.com/css?family=Roboto:400,300,600,400italic);body,h1{font-family:Roboto,Helvetica,Arial,sans-serif;line-height:30px}.popup_modals .modal_buttons .btn:hover,[hinweis]{cursor:pointer}h1{font-weight:300;font-size:30px}.copyright,[hinweis]:before,div,h1,h2,h3,input{text-align:center}*{margin:0;padding:0;box-sizing:border-box;-webkit-box-sizing:border-box;-moz-box-sizing:border-box;-webkit-font-smoothing:antialiased;-moz-font-smoothing:antialiased;-o-font-smoothing:antialiased;font-smoothing:antialiased;text-rendering:optimizeLegibility}body{font-weight:100;font-size:14px;color:#000;background:#d3d3d3}#rsscrawler button,#rsscrawler iframe,#rsscrawler input[type=text],#rsscrawler select,#rsscrawler textarea,.popup_modals .modal_buttons .btn.btn_pmry{font:400 12px/16px Roboto,Helvetica,Arial,sans-serif}.container{max-width:800px;width:100%;margin:0 auto;position:relative}[hinweis]:after,[hinweis]:before{position:absolute;bottom:150%;left:50%;visibility:hidden;-ms-filter:"progid:DXImageTransform.Microsoft.Alpha(Opacity=0)";filter:progid: DXImageTransform.Microsoft.Alpha(Opacity=0);opacity:0;pointer-events:none}#rsscrawler{background:#F9F9F9;padding:25px;margin:50px 0;box-shadow:0 0 20px 0 rgba(0,0,0,.2),0 5px 5px 0 rgba(0,0,0,.24)}#rsscrawler h1{display:block;font-size:30px;font-weight:300;margin-bottom:10px}#rsscrawler h4{margin:5px 0 15px;display:block;font-size:13px;font-weight:400}fieldset{border:none!important;margin:0 0 10px;min-width:100%;padding:0;width:100%}#rsscrawler iframe,#rsscrawler input[type=text],#rsscrawler select,#rsscrawler textarea{width:100%;border:1px solid #ccc;background:#FFF;margin:0 0 5px;padding:10px}#rsscrawler iframe,#rsscrawler input[type=text]:hover,#rsscrawler select,#rsscrawler textarea:hover{-webkit-transition:border-color .3s ease-in-out;-moz-transition:border-color .3s ease-in-out;transition:border-color .3s ease-in-out;border:1px solid #aaa}#rsscrawler button:hover,.popup_modals .modal_buttons .btn.btn_pmry:hover{-webkit-transition:background .3s ease-in-out;-moz-transition:background .3s ease-in-out}#rsscrawler select{padding-left:24px;text-align:center;text-align-last:center}#rsscrawler textarea{height:100px;max-width:100%;resize:none}#rsscrawler button{cursor:pointer;width:100%;border:none;background:#333;color:#FFF;margin:0 0 5px;padding:10px;font-size:15px}#rsscrawler button:hover{background:#43A047;transition:background-color .3s ease-in-out}#rsscrawler button:active{box-shadow:inset 0 1px 3px rgba(0,0,0,.5)}#rsscrawler input:focus,#rsscrawler textarea:focus{outline:0;border:1px solid #aaa}::-webkit-input-placeholder{color:#888}:-moz-placeholder{color:#888}::-moz-placeholder{color:#888}:-ms-input-placeholder{color:#888}[hinweis]{position:relative;z-index:2}[hinweis]:before{margin-bottom:5px;margin-left:-400px;padding:9px;width:782px;-webkit-border-radius:3px;-moz-border-radius:3px;border-radius:0;background-color:#000;background-color:hsla(0,0%,20%,.9);color:#fff;content:attr(hinweis);font-size:14px;line-height:1.2}[hinweis]:after{margin-left:-5px;width:0;border-top:5px solid #000;border-top:5px solid hsla(0,0%,20%,.9);border-right:5px solid transparent;border-left:5px solid transparent;content:" ";font-size:0;line-height:0}[hinweis]:hover:after,[hinweis]:hover:before{visibility:visible;-ms-filter:"progid:DXImageTransform.Microsoft.Alpha(Opacity=100)";filter:progid: DXImageTransform.Microsoft.Alpha(Opacity=100);opacity:1}.modal_backdrop,.popup_modals{color:#000;position:fixed;box-shadow:0 0 20px 0 rgba(0,0,0,.2),0 5px 5px 0 rgba(0,0,0,.24);top:0;right:0;left:0}.popup_modals{margin:5% auto;border-radius:0;background-color:#f5f5f5;color:#000;-webkit-transition:opacity .15s,-webkit-transform .3s;transition:opacity .15s,-webkit-transform .3s;transition:opacity .15s,transform .3s;transition:opacity .15s,transform .3s,-webkit-transform .3s}.popup_modals.modal_small{width:400px}.popup_modals.modal_medium{width:500px}.popup_modals.modal_large{width:600px}.popup_modals.fade{opacity:0;filter:alpha(opacity=0)}.popup_modals.top{-webkit-transform:translate(0,-25%);-ms-transform:translate(0,-25%);transform:translate(0,-25%)}.popup_modals.bottom{-webkit-transform:translate(0,25%);-ms-transform:translate(0,25%);transform:translate(0,25%)}.popup_modals.right{-webkit-transform:translate(25%,0);-ms-transform:translate(25%,0);transform:translate(25%,0)}.popup_modals.left{-webkit-transform:translate(-25%,0);-ms-transform:translate(-25%,0);transform:translate(-25%,0)}.popup_modals.in{opacity:1;filter:alpha(opacity=100);-webkit-transform:translate(0,0);-ms-transform:translate(0,0);transform:translate(0,0)}.popup_modals .modal_content{padding:20px}.popup_modals .modal_content .modal_input{margin-top:10px;padding:7px 10px;border-radius:4px;border:1px solid #d2dee2;box-sizing:border-box}.popup_modals .modal_buttons{padding:10px;text-transform:uppercase;letter-spacing:1px}.popup_modals .modal_buttons.right{text-align:right}.popup_modals .modal_buttons.right .btn{margin-left:5px}.popup_modals .modal_buttons.left{text-align:center}.popup_modals .modal_buttons.left .btn{margin-right:5px}.popup_modals .modal_buttons .btn{display:inline-block;color:#fff;text-decoration:none;padding:7px 10px;border-radius:0;font-size:14px}.popup_modals .modal_buttons .btn.btn_pmry{cursor:pointer;width:100%;border:none;background:#333;color:#FFF;margin:0 0 5px;padding:10px;font-size:15px}.popup_modals .modal_buttons .btn.btn_pmry:hover{background:#43A047;transition:background-color .3s ease-in-out}.popup_modals .modal_buttons .btn.btn_pmry:active{box-shadow:inset 0 1px 3px rgba(0,0,0,.5)}.popup_modals .modal_buttons .btn.btn_sdry{font:400 12px/16px Roboto,Helvetica,Arial,sans-serif;cursor:pointer;width:100%;border:none;background:#333;color:#FFF;margin:0 0 5px;padding:10px;font-size:15px}.popup_modals .modal_buttons .btn.btn_sdry:hover{background:#e74c3c;-webkit-transition:background .3s ease-in-out;-moz-transition:background .3s ease-in-out;transition:background-color .3s ease-in-out}.popup_modals .modal_buttons .btn.btn_extra{background-color:#7f8c8d}.modal_backdrop{bottom:0;-webkit-transition:all .15s;transition:all .15s}.modal_backdrop.fade{opacity:0;filter:alpha(opacity=0)}
    </style>
  </head>
  <body>
  <div class="container">
    <form id="rsscrawler" action="https://github.com/rix1337/thanks" target="_blank">
          <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAQAAAC0NkA6AAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JQAAgIMAAPn/AACA6QAAdTAAAOpgAAA6mAAAF2+SX8VGAAAAAmJLR0QA/4ePzL8AAAAJcEhZcwAACxMAAAsTAQCanBgAAAAHdElNRQfgCR0JIS9dbE8kAAAF1UlEQVRYw+2YW4xeVRXHf2vtfS7ftd9cOjMOyJQO9EK9jG29JKARjEaiNioxFnzCN+ODiRJfxPhiRGPi5UVIRCHxQYkxXkEwxijGRKoSvJeWRtJCa4tDK9POMHMuy4dzZuabc77pdKAmPrh3cpKTfbL/+/9f/7X23gf+3zbRpPJWdIAcw/4bINWmKEb+csGkfBqOH7KNWV7gFE9zjMMc43w56sjJLwcfxzGMDFvp/+RnfIrXE5Ss/Aa8LwnkKMYSKQkJaRkTw3iSLzBTfucvN5OclKQEy/k1txAAirucIMs9IyEnx/g7t+EAh15ukKKnpYR/4K0vjc+lgBScUgzjfkZgs0YoQJ7aEGSZkXGSd24Wpp9JVnNXvRd2+CxFul5acxLgnfuLmGSyNuDZusIlGD+hAxtHRwCmmWKO2fHnY1rpaDaV7cln8tfZmEFRwwZNY6QEPMG7OIkj26QLPkBMl+l25y3hF91T0h/wumzGUbZdChuGCYAx7WlXmy7weBTGeBMzYftm/1PJMNKB0iUYR7gCNpM5ihMfuWGdkNiJDwWB3r7gISkqwGCYPzK0IUzhwwNlzJfhnO/ptIROHQLtm93RFV/VYR5BV3aii6A4/bl/0v0y+Hb0meaB8clywDUUYufdFLua4dekMHkVZgnjSxtFppLxYjrvH40/tnVSQJxrK0QOB81b9QI2QLYU49aLw/SX+iIVjRzT8+F9Q7sBjRx0xQcx3X3u2QEwOcZzbLtYZOq1a6XMSxLePTE6Qui3CER+iOFpf2wATIrx/c2BLEMlZJg73Xo/4DoCDT/E8HZ3fECdSzEOri/ZxapwTkImFn3lB4p01BH7Dr0ZPVeK1F9qjCO0Wed4slEVzkiw4MFdze/RVU/kA1rvlfrXCcYnYfAmXYAcwVhctyguYf7RyfaNdLSYJrqrnHZt+J9heDCXqlzZwKRbwoKHP+iRUXmFIO8L/KEa9wTj4wO5xADSfEfz9ujO4LvuhCz7awBMeE8R2oZr0HmzDorL3whZ/9h4A6PsZnfcvin4ji5hA7auRKzxYcUXxwnCb9TMnGEcGOCxglvoAi8e1wCB4T3Bw1KHyTE9OzLdo61dHWL4Wj1fcVmK8cA6Rt5WCKfiBGUSBBoflSXyuurBA4DuLLjcU+GSY8wyPkCwnSUEAhMTrf29666LkYD223Wung9inZtiYtfSFt29mg/gMigpmzgiF7DltcGDekFMMvd0fMeOqE33Rn2xPknwEKCTgoD/RYVLgnFfDWQfd+DV03q3LmLlaTHDgh/takQ0b6+nnVp3f4umOu+IP1IByTAO4yqCHaClPbZepf/CWCpXnbGIRZ8HCL9VX2v4ZcB3tcfIdIVrjpGys1Isd4CH8K5y+1njpNHJEUau1rNrpskwd/T6aC/jhWCHKotIMW5ZFUwBIsiAt1V0FDLrLexfYPYfwb3Qd+xRLL/mz3sPM6c40N8C/bcxA169KpcCnJb32CdcPlTztRnp6CLjNO7XFN83UWYs3bDAggQE+N9L3bA7VoE9wJX2YyELz3BNtaYJ/hSc9vzVP5ZfT97PNNtnYBGGO1zRX4CrVkG0fDiQR9ZIAjlOzmw51EMF3K/WSKJg1wKZtwD/rMwjfaMCbEXJC34KME47G2X4bneCYKX+ZqQQfvXk7GkX5CHucSnUXjk35RM7W1fjGeOKc/LvvrECrEuzb0UwyxtsTs8+1zzonidYvs1LGH7zxc8hY1lARHgccCs3fQHpLnYSjB5vXLC5ksHqn4BGUdz7WouYpnYYngrvdac0c/P+d80PATrFHrZoj9EdWlxaU1JSEjKZb0+16ClA8ATGYjmWkmCcY2LZX6UnXsOfgFi9bbeodXyydeHOU1+3xzW23BwvABJkr6zobpwgabAABFcm8ZqbvpBzvHbWL0pkS8VRXNw18K9iOyN8mqG+/lJan7sPcog9PEYscxIS5WdwzPAbIASURa3+/dAcYuaBQJP63C/7H8b/XvsP5yCeXMJeZokAAAAldEVYdGRhdGU6Y3JlYXRlADIwMTYtMDktMjlUMDk6MzM6NDctMDQ6MDAyGpVfAAAAJXRFWHRkYXRlOm1vZGlmeQAyMDE2LTA5LTI5VDA5OjMzOjQ3LTA0OjAwQ0ct4wAAAABJRU5ErkJggg==" alt=""/>
          <h1>RSScrawler</h1>
          ''' + version + ''' (Projekt von <a href="https://github.com/rix1337/RSScrawler/commits" target="_blank">RiX</a>)
          <p>Legacy-Seite für Internet Explorer, Microsoft Edge, Safari, etc.</p>
          <button type="submit">Bedanken</button>
    </form>
    <form id="rsscrawler" enctype="multipart/form-data" method="post" action="..''' + prefix +'''/logleeren?wert=1">
          <h1>Log</h1>
            <iframe sandbox="allow-forms allow-same-origin allow-pointer-lock allow-scripts allow-popups allow-modals" src="./..''' + prefix +'''/log" width="800" height="240">
            Dieser Browser unterstützt keine iFrames. Stattdessen <a href = "/..''' + prefix +'''/log">/log</a> aufrufen.
          </iframe>
          <button type="submit">Leeren</button>
    </form>
    <form id="rsscrawler" enctype="multipart/form-data" method="post" action="..''' + prefix +'''/listenspeichern">
          <h1>Suchlisten</h1>
          <div hinweis="Dieser Bereich ist für die Suche auf ''' + "TW92aWUtQmxvZw==".decode('base64') + ''' zuständig."><h3>''' + "TW92aWUtQmxvZw==".decode('base64') + '''</h3></div>
          <div hinweis="Pro Zeile ein Filmtitel (wahlweise mit Erscheinungsjahr).">Filme</div>
          <textarea name="mbfilme">''' + self.getListe('MB_Filme') + '''</textarea>
          <div style='display:''' + tddiv +''';' id='dmb3'><div hinweis="Pro Zeile ein Filmtitel (wahlweise mit Erscheinungsjahr).">3D-Filme</div>
          <textarea name="mb3d">''' + self.getListe('MB_3D') + '''</textarea></div>
          <div style='display:''' + ssdiv +''';' id='dmbs'><div hinweis="Pro Zeile ein Serientitel für ganze Staffeln.">Staffeln</div>
          <textarea name="mbstaffeln">''' + self.getListe('MB_Staffeln') + '''</textarea></div>
          <div style='display:''' + mrdiv +''';' id='dmbr'><div hinweis="Pro Zeile ein Film-/Serientitel im RegEx-Format. Die Filterliste wird hierbei ignoriert!">Filme/Serien (RegEx)</div>
          <textarea name="mbregex">''' + self.getListe('MB_Regex') + '''</textarea></div>
          <div hinweis="Dieser Bereich ist für die Suche auf ''' + "U2VyaWVuSnVua2llcw==".decode('base64') + ''' zuständig."><h3>''' + "U2VyaWVuSnVua2llcw==".decode('base64') + '''</h3></div>
          <div hinweis="Pro Zeile ein Serientitel.">Serien</div>
          <textarea name="sjserien">''' + self.getListe('SJ_Serien') + '''</textarea>
          <div style='display:''' + srdiv +''';' id='dsjr'><div hinweis="Pro Zeile ein Serientitel im RegEx-Format. Die Filterliste wird hierbei ignoriert!">Serien (RegEx)</div>
          <textarea name="sjregex">''' + self.getListe('SJ_Serien_Regex') + '''</textarea></div>
          <button type="submit">Speichern</button>
    </form>
    <form id="rsscrawler" action="https://www.9kw.eu/register_87296.html" target="_blank">
          <h1>Hilfe</h1>
          <div id="regex-hinweise"><h3>Beispiele für ''' + "TW92aWUtQmxvZw==".decode('base64') + '''</h3><i>Film.*.Titel.*</i><br />Sucht nach allen Filmen die mit Film beginnen und Titel enthalten.<br /><i>.*-GROUP</i> oder <i>-GROUP</i><br />sucht nach allen Releases der GROUP.<br /><i>.*1080p.*-GROUP</i><br />sucht nach allen Full-HD Releases der GROUP.<br /><i>Film.Titel.*.DL.*.720p.*.BluRay.*-Group</i><br/>sucht nach HD-BluRay Releases von Film Titel, zweisprachig und in 720p der GROUP.<h3>Beispiele für ''' + "U2VyaWVuSnVua2llcw==".decode('base64') + '''</h3><i>DEUTSCH.*Serien.Titel.*.S01.*.720p.*-GROUP</i><br />sucht nach Releases der GROUP von Staffel 1 der Serien Titel in 720p auf Deutsch.<br /><i>Serien.Titel.*</i><br />sucht nach allen Releases von Serien Titel (nützlich, wenn man sonst HDTV aussortiert).<br /><i>Serien.Titel.*.DL.*.720p.*</i><br />sucht nach zweisprachigen Releases in 720p von Serien Titel.<br /><i>ENGLISCH.*Serien.Titel.*.1080p.*</i><br />sucht nach englischen Releases in Full-HD von Serien Titel.<br /><i>(?!(Diese|Andere)).*Serie.*.DL.*.720p.*-(GROUP|ANDEREGROUP)</i><br />sucht nach Serie (aber nicht Diese Serie oder Andere Serie), zweisprachig und in 720p und ausschließlich nach Releases von GROUP oder ANDEREGROUP.<h3>All diese Regeln lassen sich beliebig kombinieren.</h3>Falsche Regex-Einträge können allerdings das Script zum Absturz bringen!</div>
          <button type="submit">Captchas automatisch lösen</button>
    </form>
    <form id="rsscrawler" enctype="multipart/form-data" method="post" action="..''' + prefix +'''/speichern">
          <div hinweis="Hier werden sämtliche Einstellungen von RSScrawler hinterlegt. Dieses Script funktioniert nur sinnvoll, wenn Ordnerüberwachung im JDownloader aktiviert ist. Es muss weiterhin unten der richtige JDownloader Pfad gesetzt werden!">
          <h1>Einstellungen</h1></div>
          <div hinweis="Diese allgemeinen Einstellungen müssen korrekt sein!"><h3>Allgemein</h3></div>
          Pfad des JDownloaders:<div hinweis="''' + dockerhint +'''Dieser Pfad muss das exakte Verzeichnis des JDownloaders sein, sonst funktioniert das Script nicht!"><input type="text" value="''' + jdownloader +'''" name="jdownloader"''' + dockerblocker +'''></div>
          Port:<div hinweis="''' + dockerhint +'''Hier den Port des Webservers wählen."><input type="text" name="port" value="''' + port +'''"''' + dockerblocker +'''></div>
          Prefix:<div hinweis="Hier den Prefix des Webservers wählen (nützlich für Reverse-Proxies)."><input type="text" name="prefix" value="''' + prefix.replace("/", "") +'''"></div>
          Suchintervall:<div hinweis="Das Suchintervall in Minuten sollte nicht zu niedrig angesetzt werden, um keinen Ban zu riskieren. Minimum sind 3 Minuten!"><input type="text" name="interval" value="''' + interval +'''"></div>
          Pushbullet Token:<div hinweis="Um über hinzugefügte Releases informiert zu werden, hier den Pushbullet API-Token eintragen."><input type="text" name="pushbulletapi" value="''' + pushbulletapi +'''"></div>
          Hoster:<div hinweis="Hier den gewünschten Hoster wählen."><select name="hoster"><option value="Uploaded"''' + hosterul + '''>Uploaded.net</option><option value="Share-Online"''' + hosterso + '''>Share-Online.biz</option></select></div>
          <div hinweis="Dieser Bereich ist für die Suche auf ''' + "TW92aWUtQmxvZw==".decode('base64') + ''' zuständig."><h3>''' + "TW92aWUtQmxvZw==".decode('base64') + '''</h3></div>
          Auflösung:<div hinweis="Die Release-Auflösung, nach der gesucht wird."><select name="mbquality"><option value="1080p"''' + mbq1080 + '''>Full-HD</option><option value="720p"''' + mbq720 + '''>HD</option><option value="480p"''' + mbq480 + '''>SD</option></select></div>
          Filterliste:<div hinweis="Releases mit diesen Begriffen werden nicht hinzugefügt (durch Kommata getrennt)."><input type="text" name="ignore" value="''' + ignore +'''"></div>
          Suchfunktion, statt Feed nutzen:<div hinweis="Wenn aktiviert, wird die Suchfunktion des ''' + "TW92aWUtQmxvZw==".decode('base64') + ''' genutzt, da der Feed nur wenige Stunden abbildet."><select name="historical"><option value="True"''' + historicaltrue + '''>Aktiviert</option><option value="False"''' + historicalfalse + '''>Deaktiviert</option></select></div>
          Zweisprachige Releases suchen:<div hinweis="Wenn aktiviert, sucht das Script zu jedem nicht zweisprachigen Release (kein DL-Tag im Titel) ein passendes Release in 1080p mit DL Tag. Findet das Script kein Release wird dies im DEBUG-Log vermerkt. Bei der nächsten Ausführung versucht das Script dann erneut ein passendes Release zu finden. Diese Funktion ist nützlich um (durch späteres Remuxen) eine zweisprachige Bibliothek in 720p zu erhalten."><select name="enforcedl"><option value="True"''' + enforcedltrue + '''>Aktiviert</option><option value="False"''' + enforcedlfalse + '''>Deaktiviert</option></select></div>
          Filmtitel nach Retail entfernen:<div hinweis="Wenn aktiviert, werden Filme aus der Filme-Liste gestrichen, sobald ein Retail-Release gefunden wurde."><select name="cutoff"><option value="True"''' + cutofftrue + '''>Aktiviert</option><option value="False"''' + cutofffalse + '''>Deaktiviert</option></select></div>
          3D-Releases suchen:<div hinweis="Wenn aktiviert, sucht das Script zusätzlich auch nach 3D Releases (in 1080p), unabhängig von der oben gesetzten Auflösung."><select id="smb3" name="crawl3d"><option value="True"''' + crawl3dtrue + '''>Aktiviert</option><option value="False"''' + crawl3dfalse + '''>Deaktiviert</option></select></div>
          Staffeln suchen:<div hinweis="Wenn aktiviert, werden komplette Staffeln entsprechend der Staffel-Liste auf ''' + "TW92aWUtQmxvZw==".decode('base64') + ''' gesucht."><select id="smbs" name="crawlseasons"><option value="True"''' + crawlseasonstrue + '''>Aktiviert</option><option value="False"''' + crawlseasonsfalse + '''>Deaktiviert</option></select></div>
          <div style='display:''' + ssdiv +''';' id='dmbss'>Auflösung der Staffeln:<div hinweis="Die Release-Auflösung der Staffeln, nach der gesucht wird."><select name="seasonsquality"><option value="1080p"''' + msq1080 + '''>Full-HD</option><option value="720p"''' + msq720 + '''>HD</option><option value="480p"''' + msq480 + '''>SD</option></select></div>
          Quellart der Staffeln:<div hinweis="Die Quellart der Staffeln, nach der gesucht wird (BluRay, WEB, HDTV, ...)."><input type="text" name="seasonssource" value="''' + seasonssource +'''"></div></div>
          Auch per RegEx-Funktion suchen:<div hinweis="Wenn aktiviert, werden Filme aus der Filme (RegEx)-Liste nach den entsprechenden Regeln gesucht."><select id="smbr" name="mbregex"><option value="True"''' + mbregextrue + '''>Aktiviert</option><option value="False"''' + mbregexfalse + '''>Deaktiviert</option></select></div>
          <div hinweis="Dieser Bereich ist für die Suche auf ''' + "U2VyaWVuSnVua2llcw==".decode('base64') + ''' zuständig."><h3>''' + "U2VyaWVuSnVua2llcw==".decode('base64') + '''</h3></div>
          <p>Auflösung:<div hinweis="Die Release-Auflösung, nach der gesucht wird."><select name="sjquality"><option value="1080p"''' + sjq1080 + '''>Full-HD</option><option value="720p"''' + sjq720 + '''>HD</option><option value="480p"''' + sjq480 + '''>SD</option></select></div>
          Filterliste:<div hinweis="Releases mit diesen Begriffen werden nicht hinzugefügt (durch Kommata getrennt)."><input type="text" name="rejectlist" value="''' + rejectlist +'''"></div>
          Auch per RegEx-Funktion suchen:<div hinweis="Wenn aktiviert, werden Serien aus der Serien (RegEx)-Liste nach den entsprechenden Regeln gesucht."><select id="ssjr" name="sjregex"><option value="True"''' + sjregextrue + '''>Aktiviert</option><option value="False"''' + sjregexfalse + '''>Deaktiviert</option></select></div>
          <button type="submit">Speichern</button>
    </form>
    <form id="rsscrawler" enctype="multipart/form-data" method="post" action="..''' + prefix +'''/neustart?wert=1">
          <button type="submit">Neu starten</button>
    </form>
  </div>
  </body>
</html>'''

  # /log zeigt den Inhalt des RSScrawler.log
  @cherrypy.expose
  def log(self):
    # Wenn Log (noch) nicht vorhanden, Zeige Meldung
    if not os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'RSScrawler.log')):
      return "<!DOCTYPE html>\n<html lang='de'>\n<head>\n<meta charset='utf-8'>\n<meta http-equiv='refresh' content='30'>\n<meta content='width=device-width,maximum-scale=1' name='viewport'>\n<meta content='noindex, nofollow' name='robots'>\n<title>RSScrawler</title>\n<link href='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQBAMAAADt3eJSAAAABGdBTUEAALGPC/xhBQAAAAFzUkdCAK7OHOkAAAAJcEhZcwAACxMAAAsTAQCanBgAAAAwUExURUxpcQEBAQMDAwAAAAAAAAICAgAAAAAAAAAAAAEBAQQEBAEBAQMDAwEBAQICAgAAAHF9S8wAAAAPdFJOUwBkHuP2K8qzcEYVmzhVineWhWQAAAB4SURBVAjXY2CAAaabChAG4xdzIQjj//9vAiAGZ7L/f+8FINai2fb/q4A0z1uF4/9/g9XYae3/IgBWnLr8fxIDA2u7/zcd+x9AuTXC/x/s/76AgSml0N90yucABt7/nvUfF3+ZwMBqn9T/j+0/UNvBgIhO3o4AuCsAPDssr9goPWoAAABXelRYdFJhdyBwcm9maWxlIHR5cGUgaXB0YwAAeJzj8gwIcVYoKMpPy8xJ5VIAAyMLLmMLEyMTS5MUAxMgRIA0w2QDI7NUIMvY1MjEzMQcxAfLgEigSi4A6hcRdPJCNZUAAAAASUVORK5CYII=' rel='icon' type='image/png'>\n<style>\n@import url(https://fonts.googleapis.com/css?family=Roboto:400,300,600,400italic);body{font-family:Roboto,Helvetica,Arial,sans-serif;font-weight:100;font-size:14px;line-height:30px;color:#000;background:#fff}\n</style>\n</head>\n<body>\n<p></p>\n</body>\n</html>"
    else:
      # Deklariere Pfad der Logdatei (relativ)
      logfile = open(os.path.join(os.path.dirname(sys.argv[0]), 'RSScrawler.log'))
      # Nutze String um Log in HTML anzuzeigen
      output = StringIO.StringIO()
      #Füge Meta-Tag hinzu, damit Log regelmäßig neu geladen wird
      output.write("<!DOCTYPE html>\n<html lang='de'>\n<head>\n<meta charset='utf-8'>\n<meta http-equiv='refresh' content='30'>\n<meta content='width=device-width,maximum-scale=1' name='viewport'>\n<meta content='noindex, nofollow' name='robots'>\n<title>RSScrawler</title>\n<link href='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQBAMAAADt3eJSAAAABGdBTUEAALGPC/xhBQAAAAFzUkdCAK7OHOkAAAAJcEhZcwAACxMAAAsTAQCanBgAAAAwUExURUxpcQEBAQMDAwAAAAAAAAICAgAAAAAAAAAAAAEBAQQEBAEBAQMDAwEBAQICAgAAAHF9S8wAAAAPdFJOUwBkHuP2K8qzcEYVmzhVineWhWQAAAB4SURBVAjXY2CAAaabChAG4xdzIQjj//9vAiAGZ7L/f+8FINai2fb/q4A0z1uF4/9/g9XYae3/IgBWnLr8fxIDA2u7/zcd+x9AuTXC/x/s/76AgSml0N90yucABt7/nvUfF3+ZwMBqn9T/j+0/UNvBgIhO3o4AuCsAPDssr9goPWoAAABXelRYdFJhdyBwcm9maWxlIHR5cGUgaXB0YwAAeJzj8gwIcVYoKMpPy8xJ5VIAAyMLLmMLEyMTS5MUAxMgRIA0w2QDI7NUIMvY1MjEzMQcxAfLgEigSi4A6hcRdPJCNZUAAAAASUVORK5CYII=' rel='icon' type='image/png'>\n<style>\n@import url(https://fonts.googleapis.com/css?family=Roboto:400,300,600,400italic);body{font-family:Roboto,Helvetica,Arial,sans-serif;font-weight:100;font-size:14px;line-height:30px;color:#000;background:#fff}\n</style>\n</head>\n<body>\n<p>")
      # Jede Zeile der RSScrawler.log wird eingelesen. Letzter Eintrag zuerst, zwecks Übersicht
      for lines in reversed(logfile.readlines()):
        # Der Newline-Charakter \n wird um den HTML Newline-Tag <br> ergänzt
        output.write(lines.replace("\n", "</p>\n<p>"))
      output.write('</p>\n</body>\n</html>')
      return output.getvalue()

  @cherrypy.expose
  def speichern(self, jdownloader, port, prefix, interval, pushbulletapi, hoster, mbquality, ignore, historical, mbregex, cutoff, crawl3d, enforcedl, crawlseasons, seasonsquality, seasonssource, sjquality, rejectlist, sjregex):
    with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/RSScrawler.ini'), 'wb') as f:
      # RSScrawler Section:
      f.write('# RSScrawler.ini (Stand: RSScrawler ' + version + ')\n')
      f.write("\n[RSScrawler]\n")
      f.write("jdownloader = " + jdownloader.encode('utf-8') + "\n")
      f.write("port = " + port + "\n")
      f.write("prefix = " + prefix.encode('utf-8').lower() + "\n")
      if int(interval.encode('utf-8')) < 3:
        intervalchecked = '3'
      else:
        intervalchecked = interval.encode('utf-8')
      f.write("interval = " + intervalchecked + "\n")
      f.write("pushbulletapi = " + pushbulletapi.encode('utf-8') + "\n")
      f.write("hoster = " + hoster.encode('utf-8') + "\n")
      # MB Section:
      f.write("\n[MB]\n")
      f.write("quality = " + mbquality.encode('utf-8') + "\n")
      f.write("ignore = " + ignore.encode('utf-8').lower() + "\n")
      f.write("historical = " + historical.encode('utf-8') + "\n")
      f.write("regex = " + mbregex.encode('utf-8') + "\n")
      f.write("cutoff = " + cutoff.encode('utf-8') + "\n")
      f.write("crawl3d = " + crawl3d.encode('utf-8') + "\n")
      f.write("enforcedl = " + enforcedl.encode('utf-8') + "\n")
      f.write("crawlseasons = " + crawlseasons.encode('utf-8') + "\n")
      f.write("seasonsquality = " + seasonsquality.encode('utf-8') + "\n")
      f.write("seasonssource = " + seasonssource.encode('utf-8').lower() + "\n")
      # SJ Section:
      f.write("\n[SJ]\n")
      f.write("quality = " + sjquality.encode('utf-8') + "\n")
      f.write("rejectlist = " + rejectlist.encode('utf-8').lower() + "\n")
      f.write("regex = " + sjregex.encode('utf-8') + "\n")
      files.check()
      return '''<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta content="width=device-width,maximum-scale=1" name="viewport">
    <meta content="noindex, nofollow" name="robots">
    <title>RSScrawler</title>
    <link href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQBAMAAADt3eJSAAAABGdBTUEAALGPC/xhBQAAAAFzUkdCAK7OHOkAAAAJcEhZcwAACxMAAAsTAQCanBgAAAAwUExURUxpcQEBAQMDAwAAAAAAAAICAgAAAAAAAAAAAAEBAQQEBAEBAQMDAwEBAQICAgAAAHF9S8wAAAAPdFJOUwBkHuP2K8qzcEYVmzhVineWhWQAAAB4SURBVAjXY2CAAaabChAG4xdzIQjj//9vAiAGZ7L/f+8FINai2fb/q4A0z1uF4/9/g9XYae3/IgBWnLr8fxIDA2u7/zcd+x9AuTXC/x/s/76AgSml0N90yucABt7/nvUfF3+ZwMBqn9T/j+0/UNvBgIhO3o4AuCsAPDssr9goPWoAAABXelRYdFJhdyBwcm9maWxlIHR5cGUgaXB0YwAAeJzj8gwIcVYoKMpPy8xJ5VIAAyMLLmMLEyMTS5MUAxMgRIA0w2QDI7NUIMvY1MjEzMQcxAfLgEigSi4A6hcRdPJCNZUAAAAASUVORK5CYII=", rel="icon" type="image/png">
    <style>
      @import url(https://fonts.googleapis.com/css?family=Roboto:400,300,600,400italic);.copyright,[hinweis]:before,div,h1,h2,h3,input{text-align:center}*{margin:0;padding:0;box-sizing:border-box;-webkit-box-sizing:border-box;-moz-box-sizing:border-box;-webkit-font-smoothing:antialiased;-moz-font-smoothing:antialiased;-o-font-smoothing:antialiased;font-smoothing:antialiased;text-rendering:optimizeLegibility}body{font-family:Roboto,Helvetica,Arial,sans-serif;font-weight:100;font-size:14px;line-height:30px;color:#000;background:#d3d3d3}.container{max-width:800px;width:100%;margin:0 auto;position:relative}[hinweis]:after,[hinweis]:before{position:absolute;bottom:150%;left:50%}#rsscrawler button[type=submit],#rsscrawler iframe,#rsscrawler input[type=text],#rsscrawler textarea{font:400 12px/16px Roboto,Helvetica,Arial,sans-serif}#rsscrawler{background:#F9F9F9;padding:25px;margin:50px 0;box-shadow:0 0 20px 0 rgba(0,0,0,.2),0 5px 5px 0 rgba(0,0,0,.24)}#rsscrawler h1{display:block;font-size:30px;font-weight:300;margin-bottom:10px}#rsscrawler h4{margin:5px 0 15px;display:block;font-size:13px;font-weight:400}fieldset{border:none!important;margin:0 0 10px;min-width:100%;padding:0;width:100%}#rsscrawler iframe,#rsscrawler input[type=text],#rsscrawler textarea{width:100%;border:1px solid #ccc;background:#FFF;margin:0 0 5px;padding:10px}#rsscrawler iframe,#rsscrawler input[type=text]:hover,#rsscrawler textarea:hover{-webkit-transition:border-color .3s ease-in-out;-moz-transition:border-color .3s ease-in-out;transition:border-color .3s ease-in-out;border:1px solid #aaa}#rsscrawler textarea{height:100px;max-width:100%;resize:none}#rsscrawler button[type=submit]{cursor:pointer;width:100%;border:none;background:#333;color:#FFF;margin:0 0 5px;padding:10px;font-size:15px}#rsscrawler button[type=submit]:hover{background:#43A047;-webkit-transition:background .3s ease-in-out;-moz-transition:background .3s ease-in-out;transition:background-color .3s ease-in-out}#rsscrawler button[type=submit]:active{box-shadow:inset 0 1px 3px rgba(0,0,0,.5)}#rsscrawler input:focus,#rsscrawler textarea:focus{outline:0;border:1px solid #aaa}::-webkit-input-placeholder{color:#888}:-moz-placeholder{color:#888}::-moz-placeholder{color:#888}:-ms-input-placeholder{color:#888}[hinweis]{position:relative;z-index:2;cursor:pointer}[hinweis]:after,[hinweis]:before{visibility:hidden;-ms-filter:"progid:DXImageTransform.Microsoft.Alpha(Opacity=0)";filter:progid: DXImageTransform.Microsoft.Alpha(Opacity=0);opacity:0;pointer-events:none}[hinweis]:before{margin-bottom:5px;margin-left:-400px;padding:9px;width:782px;-webkit-border-radius:3px;-moz-border-radius:3px;border-radius:0;background-color:#000;background-color:hsla(0,0%,20%,.9);color:#fff;content:attr(hinweis);font-size:14px;line-height:1.2}[hinweis]:after{margin-left:-5px;width:0;border-top:5px solid #000;border-top:5px solid hsla(0,0%,20%,.9);border-right:5px solid transparent;border-left:5px solid transparent;content:" ";font-size:0;line-height:0}[hinweis]:hover:after,[hinweis]:hover:before{visibility:visible;-ms-filter:"progid:DXImageTransform.Microsoft.Alpha(Opacity=100)";filter:progid: DXImageTransform.Microsoft.Alpha(Opacity=100);opacity:1}
    </style>
  </head>
  <body>
  <div class="container">
    <form id="rsscrawler" enctype="multipart/form-data" method="post" action="../''' + prefix.encode('utf-8') + '''">
          <h1>Gespeichert!</h1>
          Die Einstellungen wurden gespeichert.
          <button type="submit">Zurück</button>
    </form>
    <form id="rsscrawler" enctype="multipart/form-data" method="post" action="neustart?wert=1">
          <h1>Hinweis</h1>
          Um einige Änderungen anzunehmen muss RSScrawler neu gestartet werden!
          <button type="submit">Neu starten</button>
    </form>
  </div>
  </body>
</html>'''

  @cherrypy.expose
  def listenspeichern(self, mbfilme, mb3d, mbstaffeln, mbregex, sjserien, sjregex):
    main = RssConfig('RSScrawler')
    prefix = main.get("prefix")
    with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/MB_Filme.txt'), 'wb') as f:
      f.write(mbfilme.encode('utf-8'))
    with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/MB_3D.txt'), 'wb') as f:
      f.write(mb3d.encode('utf-8'))
    with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/MB_Staffeln.txt'), 'wb') as f:
      f.write(mbstaffeln.encode('utf-8'))
    with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/MB_Regex.txt'), 'wb') as f:
      f.write(mbregex.encode('utf-8'))
    with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/SJ_Serien.txt'), 'wb') as f:
      f.write(sjserien.encode('utf-8'))
    with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/SJ_Serien_Regex.txt'), 'wb') as f:
      f.write(sjregex.encode('utf-8'))
    files.check()
    return '''<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta content="width=device-width,maximum-scale=1" name="viewport">
    <meta content="noindex, nofollow" name="robots">
    <title>RSScrawler</title>
    <link href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQBAMAAADt3eJSAAAABGdBTUEAALGPC/xhBQAAAAFzUkdCAK7OHOkAAAAJcEhZcwAACxMAAAsTAQCanBgAAAAwUExURUxpcQEBAQMDAwAAAAAAAAICAgAAAAAAAAAAAAEBAQQEBAEBAQMDAwEBAQICAgAAAHF9S8wAAAAPdFJOUwBkHuP2K8qzcEYVmzhVineWhWQAAAB4SURBVAjXY2CAAaabChAG4xdzIQjj//9vAiAGZ7L/f+8FINai2fb/q4A0z1uF4/9/g9XYae3/IgBWnLr8fxIDA2u7/zcd+x9AuTXC/x/s/76AgSml0N90yucABt7/nvUfF3+ZwMBqn9T/j+0/UNvBgIhO3o4AuCsAPDssr9goPWoAAABXelRYdFJhdyBwcm9maWxlIHR5cGUgaXB0YwAAeJzj8gwIcVYoKMpPy8xJ5VIAAyMLLmMLEyMTS5MUAxMgRIA0w2QDI7NUIMvY1MjEzMQcxAfLgEigSi4A6hcRdPJCNZUAAAAASUVORK5CYII=", rel="icon" type="image/png">
    <style>
      @import url(https://fonts.googleapis.com/css?family=Roboto:400,300,600,400italic);.copyright,[hinweis]:before,div,h1,h2,h3,input{text-align:center}*{margin:0;padding:0;box-sizing:border-box;-webkit-box-sizing:border-box;-moz-box-sizing:border-box;-webkit-font-smoothing:antialiased;-moz-font-smoothing:antialiased;-o-font-smoothing:antialiased;font-smoothing:antialiased;text-rendering:optimizeLegibility}body{font-family:Roboto,Helvetica,Arial,sans-serif;font-weight:100;font-size:14px;line-height:30px;color:#000;background:#d3d3d3}.container{max-width:800px;width:100%;margin:0 auto;position:relative}[hinweis]:after,[hinweis]:before{position:absolute;bottom:150%;left:50%}#rsscrawler button[type=submit],#rsscrawler iframe,#rsscrawler input[type=text],#rsscrawler textarea{font:400 12px/16px Roboto,Helvetica,Arial,sans-serif}#rsscrawler{background:#F9F9F9;padding:25px;margin:50px 0;box-shadow:0 0 20px 0 rgba(0,0,0,.2),0 5px 5px 0 rgba(0,0,0,.24)}#rsscrawler h1{display:block;font-size:30px;font-weight:300;margin-bottom:10px}#rsscrawler h4{margin:5px 0 15px;display:block;font-size:13px;font-weight:400}fieldset{border:none!important;margin:0 0 10px;min-width:100%;padding:0;width:100%}#rsscrawler iframe,#rsscrawler input[type=text],#rsscrawler textarea{width:100%;border:1px solid #ccc;background:#FFF;margin:0 0 5px;padding:10px}#rsscrawler iframe,#rsscrawler input[type=text]:hover,#rsscrawler textarea:hover{-webkit-transition:border-color .3s ease-in-out;-moz-transition:border-color .3s ease-in-out;transition:border-color .3s ease-in-out;border:1px solid #aaa}#rsscrawler textarea{height:100px;max-width:100%;resize:none}#rsscrawler button[type=submit]{cursor:pointer;width:100%;border:none;background:#333;color:#FFF;margin:0 0 5px;padding:10px;font-size:15px}#rsscrawler button[type=submit]:hover{background:#43A047;-webkit-transition:background .3s ease-in-out;-moz-transition:background .3s ease-in-out;transition:background-color .3s ease-in-out}#rsscrawler button[type=submit]:active{box-shadow:inset 0 1px 3px rgba(0,0,0,.5)}#rsscrawler input:focus,#rsscrawler textarea:focus{outline:0;border:1px solid #aaa}::-webkit-input-placeholder{color:#888}:-moz-placeholder{color:#888}::-moz-placeholder{color:#888}:-ms-input-placeholder{color:#888}[hinweis]{position:relative;z-index:2;cursor:pointer}[hinweis]:after,[hinweis]:before{visibility:hidden;-ms-filter:"progid:DXImageTransform.Microsoft.Alpha(Opacity=0)";filter:progid: DXImageTransform.Microsoft.Alpha(Opacity=0);opacity:0;pointer-events:none}[hinweis]:before{margin-bottom:5px;margin-left:-400px;padding:9px;width:782px;-webkit-border-radius:3px;-moz-border-radius:3px;border-radius:0;background-color:#000;background-color:hsla(0,0%,20%,.9);color:#fff;content:attr(hinweis);font-size:14px;line-height:1.2}[hinweis]:after{margin-left:-5px;width:0;border-top:5px solid #000;border-top:5px solid hsla(0,0%,20%,.9);border-right:5px solid transparent;border-left:5px solid transparent;content:" ";font-size:0;line-height:0}[hinweis]:hover:after,[hinweis]:hover:before{visibility:visible;-ms-filter:"progid:DXImageTransform.Microsoft.Alpha(Opacity=100)";filter:progid: DXImageTransform.Microsoft.Alpha(Opacity=100);opacity:1}
    </style>
  </head>
  <body>
  <div class="container">
    <form id="rsscrawler" enctype="multipart/form-data" method="post" action="../''' + prefix.encode('utf-8') + '''">
          <h1>Gespeichert!</h1>
          <button type="submit">Zurück</button>
    </form>
    <form id="rsscrawler" enctype="multipart/form-data" method="post" action="neustart?wert=1">
          <h1>Hinweis</h1>
          Um direkt nach den neuen Listeneinträgen zu suchen muss neu gestartet werden
          <button type="submit">Neu starten</button>
    </form>
  </div>
  </body>
</html>'''

  @cherrypy.expose
  def logleeren(self, wert):
    main = RssConfig('RSScrawler')
    prefix = main.get("prefix")
    open(os.path.join(os.path.dirname(sys.argv[0]), 'RSScrawler.log'), 'w').close()
    if wert == '1':
      return '''<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta content="width=device-width,maximum-scale=1" name="viewport">
    <meta content="noindex, nofollow" name="robots">
    <title>RSScrawler</title>
    <link href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQBAMAAADt3eJSAAAABGdBTUEAALGPC/xhBQAAAAFzUkdCAK7OHOkAAAAJcEhZcwAACxMAAAsTAQCanBgAAAAwUExURUxpcQEBAQMDAwAAAAAAAAICAgAAAAAAAAAAAAEBAQQEBAEBAQMDAwEBAQICAgAAAHF9S8wAAAAPdFJOUwBkHuP2K8qzcEYVmzhVineWhWQAAAB4SURBVAjXY2CAAaabChAG4xdzIQjj//9vAiAGZ7L/f+8FINai2fb/q4A0z1uF4/9/g9XYae3/IgBWnLr8fxIDA2u7/zcd+x9AuTXC/x/s/76AgSml0N90yucABt7/nvUfF3+ZwMBqn9T/j+0/UNvBgIhO3o4AuCsAPDssr9goPWoAAABXelRYdFJhdyBwcm9maWxlIHR5cGUgaXB0YwAAeJzj8gwIcVYoKMpPy8xJ5VIAAyMLLmMLEyMTS5MUAxMgRIA0w2QDI7NUIMvY1MjEzMQcxAfLgEigSi4A6hcRdPJCNZUAAAAASUVORK5CYII=", rel="icon" type="image/png">
    <style>
      @import url(https://fonts.googleapis.com/css?family=Roboto:400,300,600,400italic);.copyright,[hinweis]:before,div,h1,h2,h3,input{text-align:center}*{margin:0;padding:0;box-sizing:border-box;-webkit-box-sizing:border-box;-moz-box-sizing:border-box;-webkit-font-smoothing:antialiased;-moz-font-smoothing:antialiased;-o-font-smoothing:antialiased;font-smoothing:antialiased;text-rendering:optimizeLegibility}body{font-family:Roboto,Helvetica,Arial,sans-serif;font-weight:100;font-size:14px;line-height:30px;color:#000;background:#d3d3d3}.container{max-width:800px;width:100%;margin:0 auto;position:relative}[hinweis]:after,[hinweis]:before{position:absolute;bottom:150%;left:50%}#rsscrawler button[type=submit],#rsscrawler iframe,#rsscrawler input[type=text],#rsscrawler textarea{font:400 12px/16px Roboto,Helvetica,Arial,sans-serif}#rsscrawler{background:#F9F9F9;padding:25px;margin:50px 0;box-shadow:0 0 20px 0 rgba(0,0,0,.2),0 5px 5px 0 rgba(0,0,0,.24)}#rsscrawler h1{display:block;font-size:30px;font-weight:300;margin-bottom:10px}#rsscrawler h4{margin:5px 0 15px;display:block;font-size:13px;font-weight:400}fieldset{border:none!important;margin:0 0 10px;min-width:100%;padding:0;width:100%}#rsscrawler iframe,#rsscrawler input[type=text],#rsscrawler textarea{width:100%;border:1px solid #ccc;background:#FFF;margin:0 0 5px;padding:10px}#rsscrawler iframe,#rsscrawler input[type=text]:hover,#rsscrawler textarea:hover{-webkit-transition:border-color .3s ease-in-out;-moz-transition:border-color .3s ease-in-out;transition:border-color .3s ease-in-out;border:1px solid #aaa}#rsscrawler textarea{height:100px;max-width:100%;resize:none}#rsscrawler button[type=submit]{cursor:pointer;width:100%;border:none;background:#333;color:#FFF;margin:0 0 5px;padding:10px;font-size:15px}#rsscrawler button[type=submit]:hover{background:#43A047;-webkit-transition:background .3s ease-in-out;-moz-transition:background .3s ease-in-out;transition:background-color .3s ease-in-out}#rsscrawler button[type=submit]:active{box-shadow:inset 0 1px 3px rgba(0,0,0,.5)}#rsscrawler input:focus,#rsscrawler textarea:focus{outline:0;border:1px solid #aaa}::-webkit-input-placeholder{color:#888}:-moz-placeholder{color:#888}::-moz-placeholder{color:#888}:-ms-input-placeholder{color:#888}[hinweis]{position:relative;z-index:2;cursor:pointer}[hinweis]:after,[hinweis]:before{visibility:hidden;-ms-filter:"progid:DXImageTransform.Microsoft.Alpha(Opacity=0)";filter:progid: DXImageTransform.Microsoft.Alpha(Opacity=0);opacity:0;pointer-events:none}[hinweis]:before{margin-bottom:5px;margin-left:-400px;padding:9px;width:782px;-webkit-border-radius:3px;-moz-border-radius:3px;border-radius:0;background-color:#000;background-color:hsla(0,0%,20%,.9);color:#fff;content:attr(hinweis);font-size:14px;line-height:1.2}[hinweis]:after{margin-left:-5px;width:0;border-top:5px solid #000;border-top:5px solid hsla(0,0%,20%,.9);border-right:5px solid transparent;border-left:5px solid transparent;content:" ";font-size:0;line-height:0}[hinweis]:hover:after,[hinweis]:hover:before{visibility:visible;-ms-filter:"progid:DXImageTransform.Microsoft.Alpha(Opacity=100)";filter:progid: DXImageTransform.Microsoft.Alpha(Opacity=100);opacity:1}
    </style>
  </head>
  <body>
  <div class="container">
    <form id="rsscrawler" enctype="multipart/form-data" method="post" action="../''' + prefix.encode('utf-8') + '''">
          <h1>Log geleert!</h1>
          <button type="submit">Zurück</button>
    </form>
  </div>
  </body>
</html>'''
    else:
      return '''<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta content="width=device-width,maximum-scale=1" name="viewport">
    <meta content="noindex, nofollow" name="robots">
    <title>RSScrawler</title>
    <link href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQBAMAAADt3eJSAAAABGdBTUEAALGPC/xhBQAAAAFzUkdCAK7OHOkAAAAJcEhZcwAACxMAAAsTAQCanBgAAAAwUExURUxpcQEBAQMDAwAAAAAAAAICAgAAAAAAAAAAAAEBAQQEBAEBAQMDAwEBAQICAgAAAHF9S8wAAAAPdFJOUwBkHuP2K8qzcEYVmzhVineWhWQAAAB4SURBVAjXY2CAAaabChAG4xdzIQjj//9vAiAGZ7L/f+8FINai2fb/q4A0z1uF4/9/g9XYae3/IgBWnLr8fxIDA2u7/zcd+x9AuTXC/x/s/76AgSml0N90yucABt7/nvUfF3+ZwMBqn9T/j+0/UNvBgIhO3o4AuCsAPDssr9goPWoAAABXelRYdFJhdyBwcm9maWxlIHR5cGUgaXB0YwAAeJzj8gwIcVYoKMpPy8xJ5VIAAyMLLmMLEyMTS5MUAxMgRIA0w2QDI7NUIMvY1MjEzMQcxAfLgEigSi4A6hcRdPJCNZUAAAAASUVORK5CYII=", rel="icon" type="image/png">
    <style>
      @import url(https://fonts.googleapis.com/css?family=Roboto:400,300,600,400italic);.copyright,[hinweis]:before,div,h1,h2,h3,input{text-align:center}*{margin:0;padding:0;box-sizing:border-box;-webkit-box-sizing:border-box;-moz-box-sizing:border-box;-webkit-font-smoothing:antialiased;-moz-font-smoothing:antialiased;-o-font-smoothing:antialiased;font-smoothing:antialiased;text-rendering:optimizeLegibility}body{font-family:Roboto,Helvetica,Arial,sans-serif;font-weight:100;font-size:14px;line-height:30px;color:#000;background:#d3d3d3}.container{max-width:800px;width:100%;margin:0 auto;position:relative}[hinweis]:after,[hinweis]:before{position:absolute;bottom:150%;left:50%}#rsscrawler button[type=submit],#rsscrawler iframe,#rsscrawler input[type=text],#rsscrawler textarea{font:400 12px/16px Roboto,Helvetica,Arial,sans-serif}#rsscrawler{background:#F9F9F9;padding:25px;margin:50px 0;box-shadow:0 0 20px 0 rgba(0,0,0,.2),0 5px 5px 0 rgba(0,0,0,.24)}#rsscrawler h1{display:block;font-size:30px;font-weight:300;margin-bottom:10px}#rsscrawler h4{margin:5px 0 15px;display:block;font-size:13px;font-weight:400}fieldset{border:none!important;margin:0 0 10px;min-width:100%;padding:0;width:100%}#rsscrawler iframe,#rsscrawler input[type=text],#rsscrawler textarea{width:100%;border:1px solid #ccc;background:#FFF;margin:0 0 5px;padding:10px}#rsscrawler iframe,#rsscrawler input[type=text]:hover,#rsscrawler textarea:hover{-webkit-transition:border-color .3s ease-in-out;-moz-transition:border-color .3s ease-in-out;transition:border-color .3s ease-in-out;border:1px solid #aaa}#rsscrawler textarea{height:100px;max-width:100%;resize:none}#rsscrawler button[type=submit]{cursor:pointer;width:100%;border:none;background:#333;color:#FFF;margin:0 0 5px;padding:10px;font-size:15px}#rsscrawler button[type=submit]:hover{background:#43A047;-webkit-transition:background .3s ease-in-out;-moz-transition:background .3s ease-in-out;transition:background-color .3s ease-in-out}#rsscrawler button[type=submit]:active{box-shadow:inset 0 1px 3px rgba(0,0,0,.5)}#rsscrawler input:focus,#rsscrawler textarea:focus{outline:0;border:1px solid #aaa}::-webkit-input-placeholder{color:#888}:-moz-placeholder{color:#888}::-moz-placeholder{color:#888}:-ms-input-placeholder{color:#888}[hinweis]{position:relative;z-index:2;cursor:pointer}[hinweis]:after,[hinweis]:before{visibility:hidden;-ms-filter:"progid:DXImageTransform.Microsoft.Alpha(Opacity=0)";filter:progid: DXImageTransform.Microsoft.Alpha(Opacity=0);opacity:0;pointer-events:none}[hinweis]:before{margin-bottom:5px;margin-left:-400px;padding:9px;width:782px;-webkit-border-radius:3px;-moz-border-radius:3px;border-radius:0;background-color:#000;background-color:hsla(0,0%,20%,.9);color:#fff;content:attr(hinweis);font-size:14px;line-height:1.2}[hinweis]:after{margin-left:-5px;width:0;border-top:5px solid #000;border-top:5px solid hsla(0,0%,20%,.9);border-right:5px solid transparent;border-left:5px solid transparent;content:" ";font-size:0;line-height:0}[hinweis]:hover:after,[hinweis]:hover:before{visibility:visible;-ms-filter:"progid:DXImageTransform.Microsoft.Alpha(Opacity=100)";filter:progid: DXImageTransform.Microsoft.Alpha(Opacity=100);opacity:1}
    </style>
  </head>
  <body>
  <div class="container">
    <form id="rsscrawler" enctype="multipart/form-data" method="post" action="../''' + prefix.encode('utf-8') + '''">
          <h1>Log nicht geleert! Bestätigungscode fehlt.</h1>
          <button type="submit">Zurück</button>
    </form>
  </div>
  </body>
</html>'''
      
  @cherrypy.expose
  def neustart(self, wert):
    main = RssConfig('RSScrawler')
    prefix = main.get("prefix")
    if wert == '1':
      os.execl(sys.executable, sys.executable, *sys.argv)
      return '''<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta content="width=device-width,maximum-scale=1" name="viewport">
    <meta content="noindex, nofollow" name="robots">
    <title>RSScrawler</title>
    <link href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQBAMAAADt3eJSAAAABGdBTUEAALGPC/xhBQAAAAFzUkdCAK7OHOkAAAAJcEhZcwAACxMAAAsTAQCanBgAAAAwUExURUxpcQEBAQMDAwAAAAAAAAICAgAAAAAAAAAAAAEBAQQEBAEBAQMDAwEBAQICAgAAAHF9S8wAAAAPdFJOUwBkHuP2K8qzcEYVmzhVineWhWQAAAB4SURBVAjXY2CAAaabChAG4xdzIQjj//9vAiAGZ7L/f+8FINai2fb/q4A0z1uF4/9/g9XYae3/IgBWnLr8fxIDA2u7/zcd+x9AuTXC/x/s/76AgSml0N90yucABt7/nvUfF3+ZwMBqn9T/j+0/UNvBgIhO3o4AuCsAPDssr9goPWoAAABXelRYdFJhdyBwcm9maWxlIHR5cGUgaXB0YwAAeJzj8gwIcVYoKMpPy8xJ5VIAAyMLLmMLEyMTS5MUAxMgRIA0w2QDI7NUIMvY1MjEzMQcxAfLgEigSi4A6hcRdPJCNZUAAAAASUVORK5CYII=", rel="icon" type="image/png">
    <style>
      @import url(https://fonts.googleapis.com/css?family=Roboto:400,300,600,400italic);.copyright,[hinweis]:before,div,h1,h2,h3,input{text-align:center}*{margin:0;padding:0;box-sizing:border-box;-webkit-box-sizing:border-box;-moz-box-sizing:border-box;-webkit-font-smoothing:antialiased;-moz-font-smoothing:antialiased;-o-font-smoothing:antialiased;font-smoothing:antialiased;text-rendering:optimizeLegibility}body{font-family:Roboto,Helvetica,Arial,sans-serif;font-weight:100;font-size:14px;line-height:30px;color:#000;background:#d3d3d3}.container{max-width:800px;width:100%;margin:0 auto;position:relative}[hinweis]:after,[hinweis]:before{position:absolute;bottom:150%;left:50%}#rsscrawler button[type=submit],#rsscrawler iframe,#rsscrawler input[type=text],#rsscrawler textarea{font:400 12px/16px Roboto,Helvetica,Arial,sans-serif}#rsscrawler{background:#F9F9F9;padding:25px;margin:50px 0;box-shadow:0 0 20px 0 rgba(0,0,0,.2),0 5px 5px 0 rgba(0,0,0,.24)}#rsscrawler h1{display:block;font-size:30px;font-weight:300;margin-bottom:10px}#rsscrawler h4{margin:5px 0 15px;display:block;font-size:13px;font-weight:400}fieldset{border:none!important;margin:0 0 10px;min-width:100%;padding:0;width:100%}#rsscrawler iframe,#rsscrawler input[type=text],#rsscrawler textarea{width:100%;border:1px solid #ccc;background:#FFF;margin:0 0 5px;padding:10px}#rsscrawler iframe,#rsscrawler input[type=text]:hover,#rsscrawler textarea:hover{-webkit-transition:border-color .3s ease-in-out;-moz-transition:border-color .3s ease-in-out;transition:border-color .3s ease-in-out;border:1px solid #aaa}#rsscrawler textarea{height:100px;max-width:100%;resize:none}#rsscrawler button[type=submit]{cursor:pointer;width:100%;border:none;background:#333;color:#FFF;margin:0 0 5px;padding:10px;font-size:15px}#rsscrawler button[type=submit]:hover{background:#43A047;-webkit-transition:background .3s ease-in-out;-moz-transition:background .3s ease-in-out;transition:background-color .3s ease-in-out}#rsscrawler button[type=submit]:active{box-shadow:inset 0 1px 3px rgba(0,0,0,.5)}#rsscrawler input:focus,#rsscrawler textarea:focus{outline:0;border:1px solid #aaa}::-webkit-input-placeholder{color:#888}:-moz-placeholder{color:#888}::-moz-placeholder{color:#888}:-ms-input-placeholder{color:#888}[hinweis]{position:relative;z-index:2;cursor:pointer}[hinweis]:after,[hinweis]:before{visibility:hidden;-ms-filter:"progid:DXImageTransform.Microsoft.Alpha(Opacity=0)";filter:progid: DXImageTransform.Microsoft.Alpha(Opacity=0);opacity:0;pointer-events:none}[hinweis]:before{margin-bottom:5px;margin-left:-400px;padding:9px;width:782px;-webkit-border-radius:3px;-moz-border-radius:3px;border-radius:0;background-color:#000;background-color:hsla(0,0%,20%,.9);color:#fff;content:attr(hinweis);font-size:14px;line-height:1.2}[hinweis]:after{margin-left:-5px;width:0;border-top:5px solid #000;border-top:5px solid hsla(0,0%,20%,.9);border-right:5px solid transparent;border-left:5px solid transparent;content:" ";font-size:0;line-height:0}[hinweis]:hover:after,[hinweis]:hover:before{visibility:visible;-ms-filter:"progid:DXImageTransform.Microsoft.Alpha(Opacity=100)";filter:progid: DXImageTransform.Microsoft.Alpha(Opacity=100);opacity:1}
    </style>
  </head>
  <body>
  <div class="container">
    <form id="rsscrawler" enctype="multipart/form-data" method="post" action="../''' + prefix.encode('utf-8') + '''">
          <h1>Neustart ausgeführt!</h1>
          <button type="submit">Zurück</button>
    </form>
  </div>
  </body>
</html>'''
    else:
      return '''<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta content="width=device-width,maximum-scale=1" name="viewport">
    <meta content="noindex, nofollow" name="robots">
    <title>RSScrawler</title>
    <link href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQBAMAAADt3eJSAAAABGdBTUEAALGPC/xhBQAAAAFzUkdCAK7OHOkAAAAJcEhZcwAACxMAAAsTAQCanBgAAAAwUExURUxpcQEBAQMDAwAAAAAAAAICAgAAAAAAAAAAAAEBAQQEBAEBAQMDAwEBAQICAgAAAHF9S8wAAAAPdFJOUwBkHuP2K8qzcEYVmzhVineWhWQAAAB4SURBVAjXY2CAAaabChAG4xdzIQjj//9vAiAGZ7L/f+8FINai2fb/q4A0z1uF4/9/g9XYae3/IgBWnLr8fxIDA2u7/zcd+x9AuTXC/x/s/76AgSml0N90yucABt7/nvUfF3+ZwMBqn9T/j+0/UNvBgIhO3o4AuCsAPDssr9goPWoAAABXelRYdFJhdyBwcm9maWxlIHR5cGUgaXB0YwAAeJzj8gwIcVYoKMpPy8xJ5VIAAyMLLmMLEyMTS5MUAxMgRIA0w2QDI7NUIMvY1MjEzMQcxAfLgEigSi4A6hcRdPJCNZUAAAAASUVORK5CYII=", rel="icon" type="image/png">
    <style>
      @import url(https://fonts.googleapis.com/css?family=Roboto:400,300,600,400italic);.copyright,[hinweis]:before,div,h1,h2,h3,input{text-align:center}*{margin:0;padding:0;box-sizing:border-box;-webkit-box-sizing:border-box;-moz-box-sizing:border-box;-webkit-font-smoothing:antialiased;-moz-font-smoothing:antialiased;-o-font-smoothing:antialiased;font-smoothing:antialiased;text-rendering:optimizeLegibility}body{font-family:Roboto,Helvetica,Arial,sans-serif;font-weight:100;font-size:14px;line-height:30px;color:#000;background:#d3d3d3}.container{max-width:800px;width:100%;margin:0 auto;position:relative}[hinweis]:after,[hinweis]:before{position:absolute;bottom:150%;left:50%}#rsscrawler button[type=submit],#rsscrawler iframe,#rsscrawler input[type=text],#rsscrawler textarea{font:400 12px/16px Roboto,Helvetica,Arial,sans-serif}#rsscrawler{background:#F9F9F9;padding:25px;margin:50px 0;box-shadow:0 0 20px 0 rgba(0,0,0,.2),0 5px 5px 0 rgba(0,0,0,.24)}#rsscrawler h1{display:block;font-size:30px;font-weight:300;margin-bottom:10px}#rsscrawler h4{margin:5px 0 15px;display:block;font-size:13px;font-weight:400}fieldset{border:none!important;margin:0 0 10px;min-width:100%;padding:0;width:100%}#rsscrawler iframe,#rsscrawler input[type=text],#rsscrawler textarea{width:100%;border:1px solid #ccc;background:#FFF;margin:0 0 5px;padding:10px}#rsscrawler iframe,#rsscrawler input[type=text]:hover,#rsscrawler textarea:hover{-webkit-transition:border-color .3s ease-in-out;-moz-transition:border-color .3s ease-in-out;transition:border-color .3s ease-in-out;border:1px solid #aaa}#rsscrawler textarea{height:100px;max-width:100%;resize:none}#rsscrawler button[type=submit]{cursor:pointer;width:100%;border:none;background:#333;color:#FFF;margin:0 0 5px;padding:10px;font-size:15px}#rsscrawler button[type=submit]:hover{background:#43A047;-webkit-transition:background .3s ease-in-out;-moz-transition:background .3s ease-in-out;transition:background-color .3s ease-in-out}#rsscrawler button[type=submit]:active{box-shadow:inset 0 1px 3px rgba(0,0,0,.5)}#rsscrawler input:focus,#rsscrawler textarea:focus{outline:0;border:1px solid #aaa}::-webkit-input-placeholder{color:#888}:-moz-placeholder{color:#888}::-moz-placeholder{color:#888}:-ms-input-placeholder{color:#888}[hinweis]{position:relative;z-index:2;cursor:pointer}[hinweis]:after,[hinweis]:before{visibility:hidden;-ms-filter:"progid:DXImageTransform.Microsoft.Alpha(Opacity=0)";filter:progid: DXImageTransform.Microsoft.Alpha(Opacity=0);opacity:0;pointer-events:none}[hinweis]:before{margin-bottom:5px;margin-left:-400px;padding:9px;width:782px;-webkit-border-radius:3px;-moz-border-radius:3px;border-radius:0;background-color:#000;background-color:hsla(0,0%,20%,.9);color:#fff;content:attr(hinweis);font-size:14px;line-height:1.2}[hinweis]:after{margin-left:-5px;width:0;border-top:5px solid #000;border-top:5px solid hsla(0,0%,20%,.9);border-right:5px solid transparent;border-left:5px solid transparent;content:" ";font-size:0;line-height:0}[hinweis]:hover:after,[hinweis]:hover:before{visibility:visible;-ms-filter:"progid:DXImageTransform.Microsoft.Alpha(Opacity=100)";filter:progid: DXImageTransform.Microsoft.Alpha(Opacity=100);opacity:1}
    </style>
  </head>
  <body>
  <div class="container">
    <form id="rsscrawler" enctype="multipart/form-data" method="post" action="../''' + prefix.encode('utf-8') + '''">
          <h1>Neustart nicht ausgeführt! Bestätigungscode fehlt.</h1>
          <button type="submit">Zurück</button>
    </form>
  </div>
  </body>
</html>'''

      
  def getListe(self, liste):
    if not os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/' + liste + '.txt')):
      return "Liste nicht gefunden"
    else:
      file = open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/' + liste + '.txt'))
      output = StringIO.StringIO()
      # Ersetze Platzhalter für Webinterface durch Leer
      for line in file.readlines():
        output.write(line.replace("XXXXXXXXXX",""))
      return output.getvalue()

  @classmethod
  def run(cls, prefix):
    cherrypy.quickstart(cls(), '/' + prefix, os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Web/cherry.conf'))
    
  def start(self, port, prefix, docker):
    # Setzte Variable um Docker-Umgebung zu erkennen
    global dockerglobal
    dockerglobal = docker
    # Deaktiviere Cherrypy Log
    cherrypy.log.error_log.propagate = False
    cherrypy.log.access_log.propagate = False
    # Setze das Port entsprechend des Aufrufs
    cherrypy.config.update({'server.socket_port': port})
    # Setzte den Pfad der Webanwendung entsprechend des Aufrufs
    self.run(prefix)