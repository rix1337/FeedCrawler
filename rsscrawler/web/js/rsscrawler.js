app = angular.module('crwlApp', [])
    .directive('bindHtmlCompile', function ($compile) {
        return {
            restrict: "A",
            scope: {
                bindHtmlCompile: "="
            },
            link: function (scope, elem) {
                scope.$watch("bindHtmlCompile", function (newVal) {
                    elem.html('');
                    var newElem = angular.element(newVal);
                    var compileNewElem = $compile(newElem)(scope.$parent);
                    elem.append(compileNewElem);
                });
            }
        };
    });

app.controller('crwlCtrl', function ($scope, $http, $timeout) {
    $(function () {
        $('[data-toggle="tooltip"]').tooltip()
    });

    $scope.results = [
        {
            mb: {
                link: "Link",
                title: "Title"
            },
            sj: {
                id: "Link",
                title: "Title",
            }
        }
    ];

    $scope.bools = [
        {value: true, label: 'Aktiviert'},
        {value: false, label: 'Deaktiviert'},
    ];

    $scope.mb_hosters = [
        {value: '.*?share-online.*?', label: 'Share-Online'},
        {value: '.*?oboom.*?', label: 'OBOOM'},
        {value: '.*?uploaded.*?', label: 'Uploaded*'},
        {value: '.*?rapidgator.*?', label: 'Rapidgator*'},
        {value: '.*?openload.*?', label: 'Openload*'},
        {value: '.*?zippyshare.*?', label: 'Zippyshare*'},
        {value: '.*?(share-online|oboom|uploaded|rapidgator|openload|zippyshare).*?', label: 'ALLE**'},
    ];

    $scope.mb_search = [
        {value: '1', label: '30 Einträge'},
        {value: '3', label: '90 Einträge'},
        {value: '5', label: '150 Einträge'},
        {value: '10', label: '300 Einträge'},
        {value: '15', label: '450 Einträge'},
        {value: '30', label: '900 Einträge'},
        {value: '99', label: 'Alle verfügbaren Einträge (per Suchfunktion)'},
    ];

    $scope.sj_hosters = [
        {value: '.*?share-online.*?', label: 'Share-Online'},
        {value: '.*?uploaded.*?', label: 'Uploaded'},
        {value: '.*?rapidgator.*?', label: 'Rapidgator*'},
        {value: '.*', label: 'ALLE**'},
    ];

    $scope.dd_hosters = [
        {value: '.*ironfiles.*', label: 'IronFiles'},
        {value: '.*oboom.*', label: 'OBOOM'},
        {value: '.*rapidgator.*', label: 'Rapidgator'},
        {value: '.*k2s.*', label: 'Keep2Share'},
        {value: '.*filefactory.*', label: 'FileFactory'},
        {value: '.*', label: 'ALLE'},
    ];

    $scope.resolutions = [
        {value: '480p', label: '480p (SD)'},
        {value: '720p', label: '720p (HD)'},
        {value: '1080p', label: '1080p (Full-HD)'},
        {value: '2160p', label: '2160p (4K)'},
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
        },
    ];

    $scope.types_3d = [
        {value: 'hsbs', label: 'H-SBS'},
        {value: 'hou', label: 'H-OU'},
    ];

    $scope.init = getAll();

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

    $scope.resetTitle = function (title) {
        resetTitle(title);
    };

    $scope.saveLists = function () {
        setLists();
    };

    $scope.saveSettings = function () {
        setSettings();
    };

    $scope.getMyJD = function () {
        getMyJD();
    };


    function getAll() {
        getVersion()
        getLog()
        getMyJD()
        getLists()
        getSettings()
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
        $http.get('api/settings/')
            .then(function (res) {
                $scope.settings = res.data.settings;
                console.log('Einstellungen abgerufen!');
                year = (new Date).getFullYear();
                $("#year").attr("max", year);
                if ($scope.settings.general.myjd_user && $scope.settings.general.myjd_device && $scope.settings.general.myjd_device) {
                    $("#myjd").show();
                    $("#pfad").prop("disabled", true);
                }
                ;
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
                year = (new Date).getFullYear();
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
                console.log('Einstellungen gespeichert! Einige Änderungen erfordern einen Neustart.');
                showSuccess('Einstellungen gespeichert! Einige Änderungen erfordern einen Neustart.');
                getSettings();
            }, function (res) {
                $('#headingTwoOne').addClass('show');
                console.log('Konnte Einstellungen nicht speichern!');
                showDanger('Konnte Einstellungen nicht speichern!');
            });
    }

    function downloadMB(link) {
        $http.post('api/download_mb/' + link)
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
        spinSearch();
        title = $scope.search;
        $http.get('api/search/' + title)
            .then(function (res) {
                $scope.results = res.data.results;
                $(".results").show();
                $(".search").hide();
                console.log('Nach ' + title + ' gesucht!');
                getLog();
                getLists();
            }, function (res) {
                console.log('Konnte ' + title + ' nicht suchen!');
                showDanger('Konnte  ' + title + ' nicht suchen!');
            });
    }

    function showSearch() {
        $('.results').hide();
        $('.search').show();
    }

    function getMyJD() {
        $http.get('api/myjd/')
            .then(function (res) {
                $scope.myjd_state = res.data.downloader_state;
                if ($scope.myjd_state == "RUNNING") {
                    $('#myjd_state').removeClass('fa-question-circle').removeClass('fa-pause').removeClass('fa-stop').addClass('fa-play').attr('title', 'Downloads laufen');
                } else if ($scope.myjd_state == "PAUSE") {
                    $('#myjd_state').removeClass('fa-question-circle').removeClass('fa-play').removeClass('fa-stop').addClass('fa-pause').attr('title', 'Downloads pausiert');
                } else if ($scope.myjd_state == "STOPPED_STATE") {
                    $('#myjd_state').removeClass('fa-question-circle').removeClass('fa-play').removeClass('fa-pause').addClass('fa-stop').attr('title', 'Downloads angehalten');
                } else {
                    $('#myjd_state').removeClass('fa-play').removeClass('fa-pause').removeClass('fa-stop').addClass('fa-question-circle').attr('title', 'Downloadstatus unbekannt');
                }
                ;
                $scope.myjd_grabbing = res.data.grabber_collecting;
                if ($scope.myjd_grabbing) {
                    $('#myjd_grabbing').addClass('fas').addClass('fa-search');
                } else {
                    $('#myjd_grabbing').removeClass('fas').removeClass('fa-search');
                }
                ;
                $scope.myjd_downloads = res.data.packages.downloader;
                if ($scope.myjd_downloads) {
                    $('.myjd-downloads').show();
                } else {
                    $('.myjd-downloads').hide();
                }
                ;
                $scope.myjd_decrypted = res.data.packages.linkgrabber_decrypted;
                if ($scope.myjd_decrypted) {
                    $('.myjd-decrypted').show();
                } else {
                    $('.myjd-decrypted').hide();
                }
                ;
                $scope.myjd_failed = res.data.packages.linkgrabber_failed;
                if ($scope.myjd_failed) {
                    $('.myjd-failed').show();
                } else {
                    $('.myjd-failed').hide();
                }
                ;
                console.log('JDownloader abgerufen!');
            }, function (res) {
                console.log('Konnte JDownloader nicht erreichen!');
                showDanger('Konnte JDownloader nicht erreichen!');
            });
    }

    function resetTitle(title) {
        $http.delete('api/delete/' + title)
            .then(function (res) {
                console.log('Download von ' + title + ' zurückgesetzt!');
                showSuccess('Download von ' + title + ' zurückgesetzt!');
                getLog();
            }, function (res) {
                console.log('Konnte Download von ' + title + ' nicht zurück setzen!');
                showDanger('Konnte Download von ' + title + ' nicht zurück setzen!');
            });
    }

    function scrollingTitle(titleText) {
        document.title = titleText;
        setTimeout(function () {
            scrollingTitle(titleText.substr(1) + titleText.substr(0, 1));
        }, 200);
    }

    function showSuccess(message) {
        $(".alert-success").html(message);
        $(".alert-success").fadeTo(3000, 500).slideUp(500, function () {
            $(".alert-success").slideUp(500);
        });
    }

    function showInfo(message) {
        $(".alert-info").html(message);
        $(".alert-info").fadeTo(10000, 500).slideUp(500, function () {
            $(".alert-info").slideUp(500);
        });
    }

    function showDanger(message) {
        $(".alert-danger").html(message);
        $(".alert-danger").fadeTo(5000, 500).slideUp(500, function () {
            $(".alert-danger").slideUp(500);
        });
    }

    function spinSearch() {
        $("#spinner-search").fadeIn().delay(1000).fadeOut();
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

    $scope.checMyJD = function () {
        $timeout(function () {
            getMyJD();
            $scope.checMyJD();
        }, 15000)
    };

    $scope.checMyJD();

    $scope.updateChecker = function () {
        $timeout(function () {
            getVersion();
            $scope.updateChecker();
        }, 300000)
    };

    $scope.updateChecker();
});
