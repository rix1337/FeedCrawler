let app = angular.module('crwlApp', []);

app.filter('startFrom', function () {
    return function (input, start) {
        if (typeof input !== 'undefined') {
            input = Object.values(input);
            start = +start; //parse to int
            return input.slice(start);
        }
    }
});

app.controller('crwlCtrl', function ($scope, $http, $timeout) {
    $(function () {
        $('[data-toggle="tooltip"]').tooltip()
    });

    $scope.results = [];

    $scope.currentPage = 0;
    $scope.pageSize = 10;
    $scope.resLength = 0;
    $scope.numberOfPages = function () {
        if (typeof $scope.results.mb !== 'undefined') {
            $scope.resLength = Object.values($scope.results.mb).length;
            if ($scope.resLength > 10) {
                $(".btn-group").show();
            } else {
                $(".btn-group").hide();
            }
            return Math.ceil($scope.resLength / $scope.pageSize);
        }
    };

    $scope.mb_search = [
        {value: '1', label: '30 Einträge'},
        {value: '3', label: '90 Einträge'},
        {value: '5', label: '150 Einträge'},
        {value: '10', label: '300 Einträge'},
        {value: '15', label: '450 Einträge'},
        {value: '30', label: '900 Einträge'},
        {value: '99', label: 'Alle verfügbaren Einträge (per Suchfunktion)'}
    ];

    $scope.dj_genres = [
        {value: 'doku', label: 'Doku'},
        {value: 'lernen', label: 'Lernen'},
        {value: 'reality\\/entertainment', label: 'Reality\/Entertainment'},
        {value: 'sport', label: 'Sport'},
        {value: '(doku|lernen|reality\\/entertainment|sport)', label: 'ALLE (außer ReUps)'},
        {value: '.*', label: 'ALLE (inkl. ReUps)'}
    ];

    $scope.resolutions = [
        {value: '480p', label: '480p (SD)'},
        {value: '720p', label: '720p (HD)'},
        {value: '1080p', label: '1080p (Full-HD)'},
        {value: '2160p', label: '2160p (4K)'}
    ];

    $scope.sources = [
        {value: 'hdtv|hdtvrip|tvrip', label: 'HDTV'},
        {value: 'web-dl|webrip|webhd|netflix*|amazon*|itunes*', label: 'WEB'},
        {value: 'hdtv|hdtvrip|tvrip|web-dl|webrip|webhd|netflix*|amazon*|itunes*', label: 'HDTV/WEB'},
        {value: 'bluray|bd|bdrip', label: 'BluRay'},
        {value: 'web-dl|webrip|webhd|netflix*|amazon*|itunes*|bluray|bd|bdrip', label: 'Web/BluRay'},
        {
            value: 'hdtv|hdtvrip|tvrip|web-dl|webrip|webhd|netflix*|amazon*|itunes*|bluray|bd|bdrip',
            label: 'HDTV/WEB/BluRay'
        },
        {
            value: 'web-dl.*-(tvs|4sj)|webrip.*-(tvs|4sj)|webhd.*-(tvs|4sj)|netflix.*-(tvs|4sj)|amazon.*-(tvs|4sj)|itunes.*-(tvs|4sj)|bluray|bd|bdrip',
            label: 'BluRay/WebRetail (TVS/4SJ)'
        }
    ];

    $scope.types_3d = [
        {value: 'hsbs', label: 'H-SBS'},
        {value: 'hou', label: 'H-OU'}
    ];

    $scope.myjd_collapse_manual = false;
    $scope.was_grabbing = false;


    $scope.init = getAll();

    $scope.manualCollapse = function () {
        manualCollapse();
    };

    $scope.showSearch = function () {
        showSearch();
    };

    $scope.deleteLog = function () {
        deleteLog();
    };

    $scope.searchNow = function () {
        searchNow();
    };

    $scope.downloadMB = function (link) {
        downloadMB(link);
    };

    $scope.downloadSJ = function (id, special) {
        downloadSJ(id, special);
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

    $scope.myJDmove = function (linkids, uuid) {
        myJDmove(linkids, uuid);
    };

    $scope.myJDremove = function (linkids, uuid) {
        myJDremove(linkids, uuid);
    };

    $scope.myJDretry = function (linkids, uuid, links) {
        myJDretry(linkids, uuid, links);
    };

    $scope.myJDcnl = function (uuid) {
        myJDcnl(uuid)
    };

    function getAll() {
        getVersion();
        getLog();
        getLists();
        getSettings();
        getMyJD();
    }

    function manualCollapse() {
        $scope.myjd_collapse_manual = true;
    }

    function getLog() {
        $http.get('api/log/')
            .then(function (res) {
                $scope.log = res.data.log;
                console.log('Log abgerufen!');
            }, function (res) {
                console.log('Konnte Log nicht abrufen!');
                showDanger('Konnte Log nicht abrufen!');
            });
    }

    function getSettings() {
        $("#spinner-myjd").show();
        $http.get('api/settings/')
            .then(function (res) {
                $scope.settings = res.data.settings;
                console.log('Einstellungen abgerufen!');
                let year = (new Date).getFullYear();
                $("#year").attr("max", year);
                if ($scope.settings.general.myjd_user && $scope.settings.general.myjd_device && $scope.settings.general.myjd_device) {
                    $("#myjd_no_login").hide();
                } else {
                    $("#spinner-myjd").hide();
                    $("#myjd_state").hide();
                    $("#myjd_no_login").show();
                }
                if ($scope.settings.mbsj.enabled) {
                    $("#card-seasons").show();
                } else {
                    $("#card-seasons").hide();
                }
                if ($scope.settings.yt.enabled) {
                    $("#card-youtube").show();
                } else {
                    $("#card-youtube").hide();
                }
            }, function (res) {
                console.log('Konnte Einstellungen nicht abrufen!');
                showDanger('Konnte Einstellungen nicht abrufen!');
            });
    }

    function getLists() {
        $http.get('api/lists/')
            .then(function (res) {
                $scope.lists = res.data.lists;
                console.log('Listen abgerufen!');
            }, function (res) {
                console.log('Konnte Listen nicht abrufen!');
                showDanger('Konnte Listen nicht abrufen!');
            });
    }

    function getVersion() {
        $http.get('api/version/')
            .then(function (res) {
                $scope.version = res.data.version.ver;
                $("#headtitle").html('Projekt von <a href="https://github.com/rix1337/RSScrawler/releases/latest" target="_blank">RiX</a> ' + $scope.version + '<span id="updateready" style="display: none;"> - Update verfügbar!</span>');
                console.log('Dies ist der RSScrawler ' + $scope.version + ' von https://github.com/rix1337');
                $scope.update = res.data.version.update_ready;
                $scope.docker = res.data.version.docker;
                if ($scope.docker) {
                    $(".docker").prop("disabled", true);
                }
                let year = (new Date).getFullYear();
                $("#year").attr("max", year);
                if ($scope.update) {
                    $("#updateready").show();
                    scrollingTitle("RSScrawler - Update verfügbar! - ");
                    console.log('Update steht bereit! Weitere Informationen unter https://github.com/rix1337/RSScrawler/releases/latest');
                    showInfo('Update steht bereit! Weitere Informationen unter <a href="https://github.com/rix1337/RSScrawler/releases/latest" target="_blank">github.com</a>.');
                }
                console.log('Version abgerufen!');
            }, function (res) {
                console.log('Konnte Version nicht abrufen!');
                showDanger('Konnte Version nicht abrufen!');
            });
    }

    function setLists() {
        spinLists();
        $http.post('api/lists/', $scope.lists, 'application/json')
            .then(function (res) {
                console.log('Listen gespeichert! Änderungen werden im nächsten Suchlauf berücksichtigt.');
                showSuccess('Listen gespeichert! Änderungen werden im nächsten Suchlauf berücksichtigt.');
                getLists();
            }, function (res) {
                console.log('Konnte Listen nicht speichern!');
                showDanger('Konnte Listen nicht speichern!');
            });
    }

    function setSettings() {
        spinSettings();
        $http.post('api/settings/', $scope.settings, 'application/json')
            .then(function (res) {
                console.log('Einstellungen gespeichert! Neustart wird dringend empfohlen!');
                showSuccess('Einstellungen gespeichert! Neustart wird dringend empfohlen!');
                getSettings();
            }, function (res) {
                getSettings();
                console.log('Konnte Einstellungen nicht speichern! Eventuelle Hinweise in der Konsole beachten.');
                showDanger('Konnte Einstellungen nicht speichern! Eventuelle Hinweise in der Konsole beachten.');
            });
    }

    function downloadMB(link) {
        $http.post('api/download_bl/' + link)
            .then(function (res) {
                console.log('Download gestartet!');
                showSuccess('Download gestartet!');
                getLists();
            }, function (res) {
                console.log('Konnte Download nicht starten!');
                showDanger('Konnte Download nicht starten!');
            });
    }

    function downloadSJ(id, special) {
        $http.post('api/download_sj/' + id + ";" + special)
            .then(function (res) {
                console.log('Download gestartet!');
                showSuccess('Download gestartet!');
                getLists();
            }, function (res) {
                console.log('Konnte Download nicht starten!');
                showDanger('Konnte Download nicht starten!');
            });
    }

    function deleteLog() {
        spinLog();
        $http.delete('api/log/')
            .then(function (res) {
                console.log('Log geleert!');
                showSuccess('Log geleert!');
                getLog();
            }, function (res) {
                console.log('Konnte Log nicht leeren!');
                showDanger('Konnte Log nicht leeren!');
            });
    }

    function searchNow() {
        $("#spinner-search").fadeIn();
        $scope.currentPage = 0;
        let title = $scope.search;
        if (!title) {
            $scope.results = [];
            $("#spinner-search").hide();
            $(".results").hide();
        } else {
            $http.get('api/search/' + title)
                .then(function (res) {
                    $scope.results = res.data.results;
                    $scope.search = "";
                    $(".results").show();
                    console.log('Nach ' + title + ' gesucht!');
                    getLog();
                    getLists();
                    $("#spinner-search").fadeOut();
                }, function (res) {
                    console.log('Konnte ' + title + ' nicht suchen!');
                    showDanger('Konnte  ' + title + ' nicht suchen!');
                    $("#spinner-search").fadeOut();
                });
        }
    }

    function myJDupdate() {
        $('#myjd_update').addClass('blinking').addClass('isDisabled');
        $http.post('api/myjd_update/')
            .then(function (res) {
                getMyJDstate();
                console.log('JDownloader geupdatet!');
            }, function (res) {
                console.log('Konnte JDownloader nicht updaten!');
                showDanger('Konnte JDownloader nicht updaten!');
            });
    }

    function myJDstart() {
        $('#myjd_start').addClass('blinking').addClass('isDisabled');
        $http.post('api/myjd_start/')
            .then(function (res) {
                getMyJDstate();
                console.log('Download gestartet!');
            }, function (res) {
                console.log('Konnte Downloads nicht starten!');
                showDanger('Konnte Downloads nicht starten!');
            });
    }

    function myJDpause(bl) {
        $('#myjd_pause').addClass('blinking').addClass('isDisabled');
        $('#myjd_unpause').addClass('blinking').addClass('isDisabled');
        $http.post('api/myjd_pause/' + bl)
            .then(function (res) {
                getMyJDstate();
                if (bl) {
                    console.log('Download pausiert!');
                } else {
                    console.log('Download fortgesetzt!');
                }
            }, function (res) {
                console.log('Konnte Downloads nicht fortsetzen!');
                showDanger('Konnte Downloads nicht fortsetzen!');
            });
    }

    function myJDstop() {
        $('#myjd_stop').addClass('blinking').addClass('isDisabled');
        $http.post('api/myjd_stop/')
            .then(function (res) {
                getMyJDstate();
                console.log('Download angehalten!');
            }, function (res) {
                console.log('Konnte Downloads nicht anhalten!');
                showDanger('Konnte Downloads nicht anhalten!');
            });
    }

    function getMyJDstate() {
        $http.get('api/myjd_state/')
            .then(function (res) {
                $scope.myjd_state = res.data.downloader_state;
                $("#myjd_state").show();
                if ($scope.myjd_state == "RUNNING") {
                    $('#myjd_unpause').hide().removeClass('isDisabled');
                    $('#myjd_start').hide().removeClass('isDisabled');
                    $('#myjd_pause').show().removeClass('isDisabled');
                    $('#myjd_stop').show().removeClass('isDisabled');
                } else if ($scope.myjd_state == "PAUSE") {
                    $('#myjd_start').hide().removeClass('isDisabled');
                    $('#myjd_pause').hide().removeClass('isDisabled');
                    $('#myjd_stop').hide().removeClass('isDisabled');
                    $('#myjd_unpause').show().removeClass('isDisabled');
                } else {
                    $('#myjd_pause').hide().removeClass('isDisabled');
                    $('#myjd_unpause').hide().removeClass('isDisabled');
                    $('#myjd_stop').hide().removeClass('isDisabled');
                    $('#myjd_start').show().removeClass('isDisabled');
                }
                $scope.myjd_grabbing = res.data.grabber_collecting;
                if ($scope.myjd_grabbing) {
                    $('#myjd_grabbing').show();
                    $('.cnl-spinner').show();
                    $('.cnl-button').hide();
                    $('.cnl-blockers').hide();
                } else {
                    $('#myjd_grabbing').hide();
                    $('.cnl-spinner').hide();
                    $('.cnl-button').show();
                    $('.cnl-blockers').show();
                }
                $scope.update_ready = res.data.update_ready;
                if ($scope.update_ready) {
                    $('#myjd_update').show();
                } else {
                    $('#myjd_update').hide();
                }
                $('#myjd_start').removeClass('blinking');
                $('#myjd_pause').removeClass('blinking');
                $('#myjd_unpause').removeClass('blinking');
                $('#myjd_stop').removeClass('blinking');
                $('#myjd_update').removeClass('blinking').removeClass('isDisabled');
                console.log('JDownloader Status abgerufen!');
            }, function (res) {
                $("#myjd_state").hide();
                console.log('Konnte JDownloader nicht erreichen!');
                showDanger('Konnte JDownloader nicht erreichen!');
            });
    }

    function getMyJD() {
        $http.get('api/myjd/')
            .then(function (res) {
                $("#initial-loading").hide();
                $("#myjd_no_login").hide();
                $("#spinner-myjd").hide();

                $scope.myjd_state = res.data.downloader_state;
                if ($scope.myjd_state == "RUNNING") {
                    $('#myjd_unpause').hide();
                    $('#myjd_start').hide();
                    $('#myjd_pause').show();
                    $('#myjd_stop').show();
                } else if ($scope.myjd_state == "PAUSE") {
                    $('#myjd_start').hide();
                    $('#myjd_pause').hide();
                    $('#myjd_stop').hide();
                    $('#myjd_unpause').show();
                } else {
                    $('#myjd_pause').hide();
                    $('#myjd_unpause').hide();
                    $('#myjd_stop').hide();
                    $('#myjd_start').show();
                }
                $scope.myjd_downloads = res.data.packages.downloader;
                if ($scope.myjd_downloads) {
                    $('.myjd-downloads').show();
                } else {
                    $('.myjd-downloads').hide();
                }
                $scope.myjd_decrypted = res.data.packages.linkgrabber_decrypted;
                if ($scope.myjd_decrypted) {
                    $('.myjd-decrypted').show();
                } else {
                    $('.myjd-decrypted').hide();
                }
                $scope.myjd_offline = res.data.packages.linkgrabber_offline;
                if ($scope.myjd_offline) {
                    $('.myjd_offline').show();
                } else {
                    $('.myjd_offline').hide();
                }

                $scope.myjd_failed = res.data.packages.linkgrabber_failed;

                let uuids = [];
                if ($scope.myjd_failed) {
                    $('.myjd_failed').show();
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
                } else {
                    $('.myjd_failed').hide();
                }
                if ($scope.myjd_failed.length == 0) {
                    $scope.myjd_failed = false
                }
                if (!$scope.myjd_downloads && !$scope.myjd_decrypted && !$scope.myjd_failed && !$scope.myjd_offline || (typeof $scope.settings !== 'undefined' && $scope.settings.general.closed_myjd_tab)) {
                    if (!$scope.myjd_collapse_manual) {
                        $("#myjd_collapse").addClass('collapsed');
                        $("#collapseOne").removeClass('show');
                    }
                    if (typeof $scope.settings !== 'undefined' && !$scope.settings.general.closed_myjd_tab) {
                        $("#myjd_no_packages").show();
                    }
                } else {
                    $("#myjd_no_packages").hide();
                    if (!$scope.myjd_collapse_manual && (typeof $scope.settings !== 'undefined' && !$scope.settings.general.closed_myjd_tab)) {
                        $("#collapseOne").addClass('show');
                        $("#myjd_collapse").removeClass('collapsed');
                    }

                }
                if ($scope.myjd_downloads) {
                    $("#myjd_state").show();
                } else {
                    $("#myjd_state").hide();
                }
                $scope.myjd_grabbing = res.data.grabber_collecting;
                if ($scope.myjd_grabbing) {
                    $('#myjd_grabbing').show();
                    $('.cnl-spinner').show();
                    $('.cnl-button').hide();
                    $('.cnl-blockers').hide();
                    $scope.was_grabbing = true;
                    if (!$scope.myjd_collapse_manual && !$scope.settings.general.closed_myjd_tab) {
                        $("#collapseOne").addClass('show');
                        $("#myjd_collapse").removeClass('collapsed');
                    }
                } else {
                    if ($scope.was_grabbing) {
                        $('.cnl-spinner').show();
                        setTimeout(function () {
                            $('#myjd_grabbing').hide();
                            $('.cnl-spinner').hide();
                            $('.cnl-button').show();
                            $('.cnl-blockers').show();
                            $scope.was_grabbing = false;
                            getMyJD();
                        }, 15000);
                    } else {
                        setTimeout(function () {
                            $('#myjd_grabbing').hide();
                            $('.cnl-spinner').hide();
                            $('.cnl-button').show();
                            $('.cnl-blockers').show();
                        }, 1);
                    }
                }
                if ($scope.myjd_failed) {
                    $('.myjd-failed').show();
                } else {
                    $('.myjd-failed').hide();
                }
                $scope.update_ready = res.data.update_ready;
                if ($scope.update_ready) {
                    $('#myjd_update').show();
                } else {
                    $('#myjd_update').hide();
                }
                console.log('JDownloader abgerufen!');
            }, function (res) {
                $("#myjd_no_login").show();
                $scope.myjd_grabbing = null;
                $scope.myjd_downloads = null;
                $scope.myjd_decrypted = null;
                $scope.myjd_failed = null;
                console.log('Konnte JDownloader nicht erreichen!');
                showDanger('Konnte JDownloader nicht erreichen!');
            });
    }

    function myJDmove(linkids, uuid) {
        $http.post('api/myjd_move/' + linkids + "&" + uuid)
            .then(function (res) {
                getMyJD();
            }, function (res) {
                console.log('Konnte Download nicht starten!');
                showDanger('Konnte Download nicht starten!');
            });
    }

    function myJDremove(linkids, uuid) {
        $http.post('api/myjd_remove/' + linkids + "&" + uuid)
            .then(function (res) {
                for (let failed_package of $scope.myjd_failed) {
                    let existing_uuid = failed_package['uuid'];
                    if (uuid == existing_uuid) {
                        let index = $scope.myjd_failed.indexOf(failed_package);
                        $scope.myjd_failed.splice(index, 1)
                    }
                }
                getMyJD();
            }, function (res) {
                console.log('Konnte Download nicht entfernen!');
                showDanger('Konnte Download nicht entfernen!');
            });
    }

    function myJDretry(linkids, uuid, links) {
        links = btoa(links);
        $http.post('api/myjd_retry/' + linkids + "&" + uuid + "&" + links)
            .then(function (res) {
                getMyJD();
                for (let failed_package of $scope.myjd_failed) {
                    let existing_uuid = failed_package['uuid'];
                    if (uuid == existing_uuid) {
                        let index = $scope.myjd_failed.indexOf(failed_package);
                        $scope.myjd_failed.splice(index, 1)
                    }
                }
            }, function (res) {
                console.log('Konnte Download nicht erneut hinzufügen!');
                showDanger('Konnte Download nicht erneut hinzufügen!');
            });
    }

    function myJDcnl(uuid) {
        $(".cnl-button").hide();
        $(".cnl-blockers").hide();
        $(".cnl-spinner").show();
        $http.post('api/myjd_cnl/' + uuid)
            .then(function (res) {
                for (let failed_package of $scope.myjd_failed) {
                    let existing_uuid = failed_package['uuid'];
                    if (uuid == existing_uuid) {
                        let index = $scope.myjd_failed.indexOf(failed_package);
                        $scope.myjd_failed.splice(index, 1)
                    }
                }
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

    $scope.updateLog = function () {
        $timeout(function () {
            getLog();
            $scope.updateLog();
        }, 10000)
    };

    $scope.updateLog();

    $scope.checkMyJD = function () {
        $timeout(function () {
            if ($scope.settings.general.myjd_user && $scope.settings.general.myjd_device && $scope.settings.general.myjd_device) {
                getMyJD();
            }
            $scope.checkMyJD();
        }, 10000)
    };

    $scope.checkMyJD();

    $scope.updateChecker = function () {
        $timeout(function () {
            getVersion();
            $scope.updateChecker();
        }, 300000)
    };

    $scope.updateChecker();
});
