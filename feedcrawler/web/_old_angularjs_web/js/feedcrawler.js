$(function () {
    $('[data-toggle="tooltip"]').tooltip()
});

$scope.results = [];

$scope.currentMillis = Date.now();

$scope.currentPage = 0;
$scope.pageSize = 10;
$scope.resLength = 0;
$scope.numberOfPages = function () {
    if (typeof $scope.results.bl !== 'undefined') {
        $scope.resLength = Object.values($scope.results.bl).length;
        return Math.ceil($scope.resLength / $scope.pageSize);
    }
};

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

$scope.blocked_sites = false;
$scope.searching = false;

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

function spinLists() {
    $("#spinner-lists").fadeIn().delay(1000).fadeOut();
}

function spinSettings() {
    $("#spinner-settings").fadeIn().delay(1000).fadeOut();
}

$scope.showSponsorsHelp = function () {
    let offcanvas = new bootstrap.Offcanvas(document.getElementById("offcanvasBottomHelp"), {backdrop: false})
    offcanvas.show();
    new bootstrap.Collapse(document.getElementById('collapseOneZero'), {
        toggle: true
    })
    sessionStorage.setItem('fromNav', '')
    window.location.href = "#collapseOneZero";
}

