let app = angular.module('crwlApp', []);

app.filter('startFrom', function () {
    return function (input, start) {
        if (typeof input !== 'undefined') {
            if (typeof input == 'object') {
                input = Object.values(input);
                start = +start; //parse to int
                return input.slice(start);
            } else {
                start = +start; //parse to int
                return input.slice(start);
            }
        }
    }
});

app.filter('secondsToHHmmss', function ($filter) {
    return function (seconds) {
        return $filter('date')(new Date(0, 0, 0).setSeconds(seconds), 'HH:mm:ss');
    };
})

app.controller('crwlCtrl', function ($scope, $http, $timeout) {
    $(function () {
        $('[data-toggle="tooltip"]').tooltip()
    });

    $scope.results = [];

    $scope.currentPage = 0;
    $scope.pageSize = 10;
    $scope.resLength = 0;
    $scope.numberOfPages = function () {
        if (typeof $scope.results.bl !== 'undefined') {
            $scope.resLength = Object.values($scope.results.bl).length;
            return Math.ceil($scope.resLength / $scope.pageSize);
        }
    };

    $scope.currentPageLog = 0;
    $scope.pageSizeLog = 5;
    $scope.resLengthLog = 0;
    $scope.numberOfPagesLog = function () {
        if (typeof $scope.log !== 'undefined') {
            $scope.resLengthLog = $scope.log.length;
            let numPagesLog = Math.ceil($scope.resLengthLog / $scope.pageSizeLog);
            if (($scope.currentPageLog > 0) && (($scope.currentPageLog + 1) > numPagesLog)) {
                $scope.currentPageLog = numPagesLog - 1;
            }
            return numPagesLog;
        }
    };

    $scope.currentPageMyJD = 0;
    $scope.pageSizeMyJD = 3;
    $scope.resLengthMyJD = 0;
    $scope.numberOfPagesMyJD = function () {
        if (typeof $scope.myjd_packages !== 'undefined') {
            $scope.resLengthMyJD = $scope.myjd_packages.length;
            let numPagesMyJD = Math.ceil($scope.resLengthMyJD / $scope.pageSizeMyJD);
            if (($scope.currentPageMyJD > 0) && (($scope.currentPageMyJD + 1) > numPagesMyJD)) {
                $scope.currentPageMyJD = numPagesMyJD - 1;
            }
            return numPagesMyJD;
        }
    };

    $scope.helper_active = false;
    $scope.helper_available = false;

    $scope.hostnames = {
        sj: 'Nicht gesetzt!',
        dj: 'Nicht gesetzt!',
        sf: 'Nicht gesetzt!',
        by: 'Nicht gesetzt!',
        fx: 'Nicht gesetzt!',
        nk: 'Nicht gesetzt!',
        ww: 'Nicht gesetzt!',
        bl: 'Nicht gesetzt!',
        s: 'Nicht gesetzt!',
        sjbl: 'Nicht gesetzt!'
    };

    $scope.sjbl_enabled = false;

    $scope.mb_search = [
        {value: '1', label: '1 Seite'},
        {value: '3', label: '3 Seiten'},
        {value: '5', label: '5 Seiten'},
        {value: '10', label: '10 Seiten'},
        {value: '15', label: '15 Seiten'},
        {value: '30', label: '30 Seiten'}
    ];

    $scope.resolutions = [
        {value: '480p', label: '480p (SD)'},
        {value: '720p', label: '720p (HD)'},
        {value: '1080p', label: '1080p (Full-HD)'},
        {value: '2160p', label: '2160p (4K)'}
    ];

    $scope.sources = [
        {value: 'hdtv|hdtvrip|tvrip', label: 'HDTV'},
        {value: 'web|web-dl|webrip|webhd|netflix*|amazon*|itunes*', label: 'WEB'},
        {value: 'hdtv|hdtvrip|tvrip|web|web-dl|webrip|webhd|netflix*|amazon*|itunes*', label: 'HDTV/WEB'},
        {value: 'bluray|bd|bdrip', label: 'BluRay'},
        {value: 'web|web-dl|webrip|webhd|netflix*|amazon*|itunes*|bluray|bd|bdrip', label: 'Web/BluRay'},
        {
            value: 'hdtv|hdtvrip|tvrip|web|web-dl|webrip|webhd|netflix*|amazon*|itunes*|bluray|bd|bdrip',
            label: 'HDTV/WEB/BluRay'
        },
        {
            value: 'web.*-(tvs|4sj|tvr)|web-dl.*-(tvs|4sj|tvr)|webrip.*-(tvs|4sj|tvr)|webhd.*-(tvs|4sj|tvr)|netflix.*-(tvs|4sj|tvr)|amazon.*-(tvs|4sj|tvr)|itunes.*-(tvs|4sj|tvr)|bluray|bd|bdrip',
            label: 'BluRay/WebRetail (TVS/4SJ/TvR)'
        }
    ];

    $scope.crawltimes = false;
    $scope.blocked_sites = false;
    $scope.cnl_active = false;
    $scope.myjd_connection_error = false;
    $scope.myjd_collapse_manual = false;
    $scope.searching = false;
    $scope.starting = false;
    $scope.myjd_state = false;
    $scope.myjd_packages = [];
    $scope.time = 0;

    $scope.loglength = 65;
    $scope.longlog = false;

    $(window).resize(function () {
        setAccordionWidth();
    });

    function setAccordionWidth() {
        $scope.windowWidth = $(window).width();
        if ($scope.windowWidth <= 768) {
            $scope.accordionlength = 45;
        } else {
            $scope.accordionlength = 85;
        }
    }

    $scope.longerLog = function () {
        $scope.loglength = 999;
        $scope.longlog = true;
    };

    $scope.shorterLog = function () {
        $scope.loglength = 65;
        $scope.longlog = false;
    };

    $scope.init = getAll();

    $scope.manualCollapse = function () {
        manualCollapse();
    };

    $scope.deleteLog = function () {
        deleteLog();
    };

    $scope.deleteLogRow = function (row) {
        deleteLogRow(row);
    };


    $scope.searchNow = function () {
        searchNow();
    };

    $scope.downloadBL = function (payload) {
        downloadBL(payload);
    };

    $scope.downloadSJ = function (payload) {
        downloadSJ(payload);
    };

    $scope.saveLists = function () {
        setLists();
    };

    $scope.saveSettings = function () {
        setSettings();
    };

    $scope.myJDupdate = function () {
        myJDupdate();
    };


    $scope.myJDstart = function () {
        myJDstart();
    };

    $scope.myJDpause = function (bl) {
        myJDpause(bl);
    };

    $scope.myJDstop = function () {
        myJDstop();
    };

    $scope.getMyJDstate = function () {
        getMyJDstate();
    };


    $scope.getMyJD = function () {
        getMyJD();
    };

    $scope.startNow = function () {
        startNow();
    };

    $scope.myJDmove = function (linkids, uuid) {
        myJDmove(linkids, uuid);
    };

    $scope.myJDremove = function (linkids, uuid) {
        myJDremove(linkids, uuid);
    };

    $scope.myJDremove = function (linkids, uuid) {
        myJDremove(linkids, uuid);
    };

    $scope.internalRemove = function (name) {
        internalRemove(name);
    };

    $scope.myJDretry = function (linkids, uuid, links) {
        myJDretry(linkids, uuid, links)
    };

    $scope.myJDcnl = function (uuid) {
        myJDcnl(uuid)
    };

    $scope.internalCnl = function (name, password) {
        internalCnl(name, password)
    };

    $scope.getLists = function () {
        getLists();
    }

    $scope.getSettings = function () {
        getSettings();
    }

    $scope.getBlockedSites = function () {
        getBlockedSites();
    }

    function getAll() {
        getHostNames();
        getVersion();
        getMyJD();
        getLog();
        getCrawlTimes();
        getSettings();
    }

    function countDown(seconds) {
        if (seconds === 0) {
            return;
        } else {
            seconds--;
        }
        $scope.time = seconds;
        $timeout(function () {
            countDown(seconds)
        }, 1000);
    }

    function manualCollapse() {
        $scope.myjd_collapse_manual = true;
    }

    function getLog() {
        $http.get('api/log/')
            .then(function (res) {
                $scope.log = res.data.log;
                console.log('Log abgerufen!');
            }, function () {
                console.log('Konnte Log nicht abrufen!');
                showDanger('Konnte Log nicht abrufen!');
            });
    }

    function getSettings() {
        $http.get('api/settings/')
            .then(function (res) {
                $scope.settings = res.data.settings;
                console.log('Einstellungen abgerufen!');
                let year = (new Date).getFullYear();
                $("#year").attr("max", year);
                $scope.myjd_connection_error = !($scope.settings.general.myjd_user && $scope.settings.general.myjd_device && $scope.settings.general.myjd_device);
                $scope.pageSizeMyJD = $scope.settings.general.packages_per_myjd_page;
            }, function () {
                console.log('Konnte Einstellungen nicht abrufen!');
                showDanger('Konnte Einstellungen nicht abrufen!');
            });
    }

    function getLists() {
        $http.get('api/lists/')
            .then(function (res) {
                $scope.lists = res.data.lists;
                console.log('Listen abgerufen!');
            }, function () {
                console.log('Konnte Listen nicht abrufen!');
                showDanger('Konnte Listen nicht abrufen!');
            });
    }

    function getCrawlTimes() {
        $http.get('api/crawltimes/')
            .then(function (res) {
                $scope.starting = false;
                $scope.crawltimes = res.data.crawltimes;
                console.log('Laufzeiten abgerufen!');
            }, function () {
                console.log('Konnte Laufzeiten nicht abrufen!');
                showDanger('Konnte Laufzeiten nicht abrufen!');
            });
    }

    function getHostNames() {
        $http.get('api/hostnames/')
            .then(function (res) {
                $scope.hostnames = res.data.hostnames;
                not_set = 'Nicht gesetzt!'
                $scope.sjbl_enabled = !(($scope.hostnames.bl === not_set && $scope.hostnames.s !== not_set) || ($scope.hostnames.bl !== not_set && $scope.hostnames.s === not_set));
                console.log('Hostnamen abgerufen!');
            }, function () {
                console.log('Konnte Hostnamen nicht abrufen!');
                showDanger('Konnte Hostnamen nicht abrufen!');
            });
    }

    function getBlockedSites() {
        $http.get('api/blocked_sites/')
            .then(function (res) {
                $scope.blocked_sites = res.data.blocked_sites;
                console.log('Blockierte Seiten abgerufen!');
            }, function () {
                console.log('Konnte blockierte Seiten nicht abrufen!');
                showDanger('Konnte blockierte Seiten nicht abrufen!');
            });
    }

    function getVersion() {
        $http.get('api/version/')
            .then(function (res) {
                $scope.version = res.data.version.ver;
                console.log('Dies ist der FeedCrawler ' + $scope.version + ' von https://github.com/rix1337');
                $scope.update = res.data.version.update_ready;
                $scope.docker = res.data.version.docker;
                if ($scope.docker) {
                    $(".docker").prop("disabled", true);
                }
                $scope.helper_active = res.data.version.helper_active;
                if ($scope.helper_active) {
                    $.get("http://127.0.0.1:9666/", function (data) {
                        $scope.helper_available = (data === 'JDownloader');
                        if ($scope.helper_available) {
                            console.log("Click'n'Load des FeedCrawler Sponsors Helper ist verfügbar!");
                        }
                    });
                }
                let year = (new Date).getFullYear();
                $("#year").attr("max", year);
                if ($scope.update) {
                    scrollingTitle("FeedCrawler - Update verfügbar! - ");
                    console.log('Update steht bereit! Weitere Informationen unter https://github.com/rix1337/FeedCrawler/releases/latest');
                    showInfo('Update steht bereit! Weitere Informationen unter <a href="https://github.com/rix1337/FeedCrawler/releases/latest" target="_blank">github.com</a>.');
                }
                console.log('Version abgerufen!');
            }, function () {
                console.log('Konnte Version nicht abrufen!');
                showDanger('Konnte Version nicht abrufen!');
            });
    }

    function setLists() {
        spinLists();
        $http.post('api/lists/', $scope.lists, 'application/json')
            .then(function () {
                console.log('Listen gespeichert! Änderungen werden im nächsten Suchlauf berücksichtigt.');
                showSuccess('Listen gespeichert! Änderungen werden im nächsten Suchlauf berücksichtigt.');
                getLists();
            }, function () {
                console.log('Konnte Listen nicht speichern!');
                showDanger('Konnte Listen nicht speichern!');
            });
    }

    function setSettings() {
        spinSettings();
        $http.post('api/settings/', $scope.settings, 'application/json')
            .then(function () {
                console.log('Einstellungen gespeichert! Neustart wird dringend empfohlen!');
                showSuccess('Einstellungen gespeichert! Neustart wird dringend empfohlen!');
                getSettings();
            }, function () {
                getSettings();
                console.log('Konnte Einstellungen nicht speichern! Eventuelle Hinweise in der Konsole beachten.');
                showDanger('Konnte Einstellungen nicht speichern! Eventuelle Hinweise in der Konsole beachten.');
            });
    }

    function downloadBL(payload) {
        showInfoLong("Starte Download...");
        $http.post('api/download_bl/' + payload)
            .then(function () {
                console.log('Download gestartet!');
                showSuccess('Download gestartet!');
                getLists();
                $(".alert-info").slideUp(500);
            }, function () {
                console.log('Konnte Download nicht starten!');
                showDanger('Konnte Download nicht starten!');
                $(".alert-info").slideUp(500);
            });
    }

    function downloadSJ(payload) {
        showInfoLong("Starte Download...");
        $http.post('api/download_sj/' + payload)
            .then(function () {
                console.log('Download gestartet!');
                showSuccess('Download gestartet!');
                getLists();
                $(".alert-info").slideUp(500);
            }, function () {
                console.log('Konnte Download nicht starten!');
                showDanger('Konnte Download nicht starten!');
                $(".alert-info").slideUp(500);
            });
    }

    function deleteLog() {
        spinLog();
        $http.delete('api/log/')
            .then(function () {
                console.log('Log geleert!');
                showSuccess('Log geleert!');
                getLog();
            }, function () {
                console.log('Konnte Log nicht leeren!');
                showDanger('Konnte Log nicht leeren!');
            });
    }

    function deleteLogRow(title) {
        title = btoa(title);
        $http.delete('api/log_entry/' + title)
            .then(function () {
                console.log('Logeintrag gelöscht!');
                showSuccess('Logeintrag gelöscht!');
                getLog();
            }, function () {
                console.log('Konnte Logeintrag nicht löschen!');
                showDanger('Konnte Logeintrag nicht löschen!');
            });
    }

    function searchNow() {
        $("#spinner-search").fadeIn();
        $scope.currentPage = 0;
        let title = $scope.search;
        $scope.searching = true;
        if (!title) {
            $scope.results = [];
            $scope.resLength = 0;
            $scope.searching = false;
        } else {
            $http.get('api/search/' + title)
                .then(function (res) {
                    $scope.results = res.data.results;
                    $scope.resLength = Object.values($scope.results.bl).length;
                    $scope.search = "";
                    console.log('Nach ' + title + ' gesucht!');
                    getLog();
                    getLists();
                    $("#spinner-search").fadeOut();
                    $scope.searching = false;
                }, function () {
                    console.log('Konnte ' + title + ' nicht suchen!');
                    showDanger('Konnte  ' + title + ' nicht suchen!');
                    $("#spinner-search").fadeOut();
                });
        }
    }

    function myJDupdate() {
        $('#myjd_update').addClass('blinking').addClass('isDisabled');
        $http.post('api/myjd_update/')
            .then(function () {
                getMyJDstate();
                console.log('JDownloader geupdatet!');
            }, function () {
                console.log('Konnte JDownloader nicht updaten!');
                showDanger('Konnte JDownloader nicht updaten!');
            });
    }

    function myJDstart() {
        $('#myjd_start').addClass('blinking').addClass('isDisabled');
        $http.post('api/myjd_start/')
            .then(function () {
                getMyJDstate();
                console.log('Download gestartet!');
            }, function () {
                console.log('Konnte Downloads nicht starten!');
                showDanger('Konnte Downloads nicht starten!');
            });
    }

    function myJDpause(bl) {
        $('#myjd_pause').addClass('blinking').addClass('isDisabled');
        $('#myjd_unpause').addClass('blinking').addClass('isDisabled');
        $http.post('api/myjd_pause/' + bl)
            .then(function () {
                getMyJDstate();
                if (bl) {
                    console.log('Download pausiert!');
                } else {
                    console.log('Download fortgesetzt!');
                }
            }, function () {
                console.log('Konnte Downloads nicht fortsetzen!');
                showDanger('Konnte Downloads nicht fortsetzen!');
            });
    }

    function myJDstop() {
        $('#myjd_stop').addClass('blinking').addClass('isDisabled');
        $http.post('api/myjd_stop/')
            .then(function () {
                getMyJDstate();
                console.log('Download angehalten!');
            }, function () {
                console.log('Konnte Downloads nicht anhalten!');
                showDanger('Konnte Downloads nicht anhalten!');
            });
    }

    function getMyJDstate() {
        $http.get('api/myjd_state/')
            .then(function (res) {
                $scope.myjd_state = res.data.downloader_state;
                $scope.myjd_grabbing = res.data.grabber_collecting;
                $scope.update_ready = res.data.update_ready;
                $('#myjd_start').removeClass('blinking').removeClass('isDisabled');
                $('#myjd_pause').removeClass('blinking').removeClass('isDisabled');
                $('#myjd_unpause').removeClass('blinking').removeClass('isDisabled');
                $('#myjd_stop').removeClass('blinking').removeClass('isDisabled');
                $('#myjd_update').removeClass('blinking').removeClass('isDisabled');
                console.log('JDownloader Status abgerufen!');
            }, function () {
                console.log('Konnte JDownloader nicht erreichen!');
                showDanger('Konnte JDownloader nicht erreichen!');
            });
    }

    function getMyJD() {
        $http.get('api/myjd/')
            .then(function (res) {
                $scope.myjd_connection_error = false;
                $scope.myjd_state = res.data.downloader_state;
                $scope.myjd_downloads = res.data.packages.downloader;
                $scope.myjd_decrypted = res.data.packages.linkgrabber_decrypted;
                $scope.myjd_offline = res.data.packages.linkgrabber_offline;
                $scope.myjd_failed = res.data.packages.linkgrabber_failed;
                $scope.to_decrypt = res.data.packages.to_decrypt;

                let uuids = [];
                if ($scope.myjd_failed) {
                    for (let existing_package of $scope.myjd_failed) {
                        let uuid = existing_package['uuid'];
                        uuids.push(uuid)
                    }
                    const failed_packages = Object.entries(res.data.packages.linkgrabber_failed);
                    for (let failed_package of failed_packages) {
                        let uuid = failed_package[1]['uuid'];
                        if (!uuids.includes(uuid)) {
                            $scope.myjd_failed.push(failed_package[1])
                        }
                    }
                }
                let names = [];
                if ($scope.to_decrypt) {
                    for (let existing_package of $scope.to_decrypt) {
                        let name = existing_package['name'];
                        names.push(name)
                    }
                    const to_decrypt = Object.entries(res.data.packages.to_decrypt);
                    for (let failed_package of to_decrypt) {
                        let name = failed_package[1]['name'];
                        if (!names.includes(name)) {
                            $scope.to_decrypt.push(failed_package[1])
                        }
                    }
                }
                $scope.myjd_grabbing = res.data.grabber_collecting;
                if ($scope.myjd_grabbing) {
                    if (!$scope.myjd_collapse_manual && !$scope.settings.general.closed_myjd_tab) {
                        $("#collapseOne").addClass('show');
                        $("#myjd_collapse").removeClass('collapsed');
                    }
                }
                $scope.update_ready = res.data.update_ready;

                $scope.myjd_packages = [];
                if ($scope.myjd_failed) {
                    for (let p of $scope.myjd_failed) {
                        p.type = "failed";
                        $scope.myjd_packages.push(p);
                    }
                }
                if ($scope.to_decrypt) {
                    let first = true;
                    for (let p of $scope.to_decrypt) {
                        p.type = "to_decrypt";
                        p.first = first;
                        first = false;
                        $scope.myjd_packages.push(p);
                    }
                }
                if ($scope.myjd_offline) {
                    for (let p of $scope.myjd_offline) {
                        p.type = "offline";
                        $scope.myjd_packages.push(p);
                    }
                }
                if ($scope.myjd_decrypted) {
                    for (let p of $scope.myjd_decrypted) {
                        p.type = "decrypted";
                        $scope.myjd_packages.push(p);
                    }
                }
                if ($scope.myjd_downloads) {
                    for (let p of $scope.myjd_downloads) {
                        p.type = "online";
                        $scope.myjd_packages.push(p);
                    }
                }

                if ($scope.myjd_packages.length === 0 || (typeof $scope.settings !== 'undefined' && $scope.settings.general.closed_myjd_tab)) {
                    if (!$scope.myjd_collapse_manual) {
                        $("#myjd_collapse").addClass('collapsed');
                        $("#collapseOne").removeClass('show');
                    }
                } else {
                    if (!$scope.myjd_collapse_manual && (typeof $scope.settings !== 'undefined' && !$scope.settings.general.closed_myjd_tab)) {
                        $("#collapseOne").addClass('show');
                        $("#myjd_collapse").removeClass('collapsed');
                    }
                }

                console.log('JDownloader abgerufen!');
            }, function () {
                $scope.myjd_grabbing = null;
                $scope.myjd_downloads = null;
                $scope.myjd_decrypted = null;
                $scope.myjd_failed = null;
                $scope.myjd_connection_error = true;
                console.log('Konnte JDownloader nicht erreichen!');
                showDanger('Konnte JDownloader nicht erreichen!');
            });
    }

    function startNow() {
        showInfoLong("Starte Suchlauf...");
        $scope.starting = true;
        $http.post('api/start_now/')
            .then(function () {
                $(".alert-info").slideUp(1500);
            }, function () {
                $scope.starting = false;
                console.log('Konnte Suchlauf nicht starten!');
                showDanger('Konnte Suchlauf nicht starten!');
                $(".alert-info").slideUp(1500);
            });
    }

    function myJDmove(linkids, uuid) {
        showInfoLong("Starte Download...");
        $http.post('api/myjd_move/' + linkids + "&" + uuid)
            .then(function () {
                getMyJD();
                $(".alert-info").slideUp(1500);
            }, function () {
                console.log('Konnte Download nicht starten!');
                showDanger('Konnte Download nicht starten!');
                $(".alert-info").slideUp(1500);
            });
    }

    function myJDremove(linkids, uuid) {
        showInfoLong("Lösche Download...");
        $http.post('api/myjd_remove/' + linkids + "&" + uuid)
            .then(function () {
                if ($scope.myjd_failed) {
                    for (let failed_package of $scope.myjd_failed) {
                        let existing_uuid = failed_package['uuid'];
                        if (uuid === existing_uuid) {
                            let index = $scope.myjd_failed.indexOf(failed_package);
                            $scope.myjd_failed.splice(index, 1)
                        }
                    }
                }
                getMyJD();
                $(".alert-info").slideUp(1500);
            }, function () {
                console.log('Konnte Download nicht löschen!');
                showDanger('Konnte Download nicht löschen!');
                $(".alert-info").slideUp(1500);
            });
    }

    function internalRemove(name) {
        showInfoLong("Lösche Download...");
        $http.post('api/internal_remove/' + name)
            .then(function () {
                if ($scope.to_decrypt) {
                    for (let failed_package of $scope.to_decrypt) {
                        let existing_name = failed_package['name'];
                        if (name === existing_name) {
                            let index = $scope.to_decrypt.indexOf(failed_package);
                            $scope.to_decrypt.splice(index, 1)
                        }
                    }
                }
                getMyJD();
                $(".alert-info").slideUp(1500);
            }, function () {
                console.log('Konnte Download nicht löschen!');
                showDanger('Konnte Download nicht löschen!');
                $(".alert-info").slideUp(1500);
            });
    }

    function myJDretry(linkids, uuid, links) {
        showInfoLong("Füge Download erneut hinzu...");
        links = btoa(links);
        $http.post('api/myjd_retry/' + linkids + "&" + uuid + "&" + links)
            .then(function () {
                if ($scope.myjd_failed) {
                    for (let failed_package of $scope.myjd_failed) {
                        let existing_uuid = failed_package['uuid'];
                        if (uuid === existing_uuid) {
                            let index = $scope.myjd_failed.indexOf(failed_package);
                            $scope.myjd_failed.splice(index, 1)
                        }
                    }
                }
                getMyJD();
                $(".alert-info").slideUp(1500);
            }, function () {
                console.log('Konnte Download nicht erneut hinzufügen!');
                showDanger('Konnte Download nicht erneut hinzufügen!');
                $(".alert-info").slideUp(1500);
            });
    }

    function myJDcnl(uuid) {
        showInfoLong("Warte auf Click'n'Load...");
        $scope.cnl_active = true;
        countDown(60);
        $http.post('api/myjd_cnl/' + uuid)
            .then(function () {
                $scope.cnl_active = false;
                if ($scope.myjd_failed) {
                    for (let failed_package of $scope.myjd_failed) {
                        let existing_uuid = failed_package['uuid'];
                        if (uuid === existing_uuid) {
                            let index = $scope.myjd_failed.indexOf(failed_package);
                            $scope.myjd_failed.splice(index, 1)
                        }
                    }
                }
                $(".alert-info").slideUp(500);
                $scope.time = 0;
            }).catch(function () {
            showDanger("Click'n'Load nicht durchgeführt!");
            $scope.cnl_active = false;
            $(".alert-info").slideUp(500);
            $scope.time = 0;
        });
    }

    function internalCnl(name, password) {
        showInfoLong("Warte auf Click'n'Load...");
        $scope.cnl_active = true;
        countDown(60);
        $http.post('api/internal_cnl/' + name + "&" + password)
            .then(function () {
                $scope.cnl_active = false;
                if ($scope.to_decrypt) {
                    for (let failed_package of $scope.to_decrypt) {
                        let existing_name = failed_package['name'];
                        if (name === existing_name) {
                            let index = $scope.to_decrypt.indexOf(failed_package);
                            $scope.to_decrypt.splice(index, 1)
                        }
                    }
                }
                $(".alert-info").slideUp(500);
                $scope.time = 0;
            }).catch(function () {
            showDanger("Click'n'Load nicht durchgeführt!");
            $scope.cnl_active = false;
            $(".alert-info").slideUp(500);
            $scope.time = 0;
        });
    }

    function scrollingTitle(titleText) {
        document.title = titleText;
        setTimeout(function () {
            scrollingTitle(titleText.substr(1) + titleText.substr(0, 1));
        }, 200);
    }

    function showSuccess(message) {
        $(".alert-success").html(message).fadeTo(3000, 500).slideUp(500, function () {
            $(".alert-success").slideUp(500);
        });
    }

    function showInfo(message) {
        $(".alert-info").html(message).fadeTo(10000, 500).slideUp(500, function () {
            $(".alert-info").slideUp(500);
        });
    }

    function showInfoLong(message) {
        $(".alert-info").html(message).show();
    }

    function showDanger(message) {
        $(".alert-danger").html(message).fadeTo(5000, 500).slideUp(500, function () {
            $(".alert-danger").slideUp(500);
        });
    }

    function spinLog() {
        $("#spinner-log").fadeIn().delay(1000).fadeOut();
    }

    function spinLists() {
        $("#spinner-lists").fadeIn().delay(1000).fadeOut();
    }

    function spinSettings() {
        $("#spinner-settings").fadeIn().delay(1000).fadeOut();
    }

    $scope.updateTime = function () {
        $timeout(function () {
            $scope.now = Date.now();
            $scope.updateTime();
        }, 1000)
    };

    $scope.updateTime();

    $scope.checkMyJD = function () {
        $timeout(function () {
            if (!$scope.cnl_active) {
                if (typeof $scope.settings !== 'undefined') {
                    if ($scope.settings.general.myjd_user && $scope.settings.general.myjd_device && $scope.settings.general.myjd_device) {
                        getMyJD();
                    }
                }
            }
            $scope.checkMyJD();
        }, 15000)
    };

    $scope.checkMyJD();

    $scope.updateLog = function () {
        $timeout(function () {
            if (!$scope.cnl_active) {
                getLog();
            }
            $scope.updateLog();
        }, 15000)
    };

    $scope.updateLog();

    $scope.updateCrawlTimes = function () {
        $timeout(function () {
            if (!$scope.cnl_active) {
                getCrawlTimes();
            }
            $scope.updateCrawlTimes();
        }, 15000)
    };

    $scope.updateCrawlTimes();

    $scope.updateChecker = function () {
        $timeout(function () {
            if (!$scope.cnl_active) {
                getVersion();
            }
            $scope.updateChecker();
        }, 300000)
    };

    $scope.updateChecker();
})
;
