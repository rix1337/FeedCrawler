$(function () {
    $('[data-toggle="tooltip"]').tooltip()
});

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

function spinSettings() {
    $("#spinner-settings").fadeIn().delay(1000).fadeOut();
}

