app = angular.module('crwlApp', ['ngSanitize']);

app.controller('crwlCtrl', function($scope, $http, $timeout){
    $(function () {
        $('[data-toggle="tooltip"]').tooltip()
      })

    $scope.bools = [
        {value: true, label: 'Aktiviert'},
        {value: false, label: 'Deaktiviert'},
    ];

    $scope.hosters = [
        {value: 'Uploaded', label: 'Uploaded'},
        {value: 'Share-Online', label: 'Share-Online'},
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
        {value: 'hdtv|hdtvrip|tvrip|web-dl|webrip|webhd|netflix*|amazon*|itunes*|bluray|bd|bdrip', label: 'HDTV/WEB/BluRay'},
        {value: 'web-dl.*-(tvs|4sj)|webrip.*-(tvs|4sj)|webhd.*-(tvs|4sj)|netflix.*-(tvs|4sj)|amazon.*-(tvs|4sj)|itunes.*-(tvs|4sj)|bluray|bd|bdrip', label: 'BluRay/WebRetail (TVS/4SJ)'},
    ];

    $scope.init = getAll();

    $scope.deleteLog = function() {
        deleteLog();
    }

    $scope.saveLists = function() {
        setLists();
    }

    $scope.saveSettings = function() {
        setSettings();
    }

    function getAll() {
        $http.get('api/all/')
        .then(function(res){
            $scope.version = res.data.version.ver;
            $(".versioninfo").append(" " + $scope.version);
            console.log('Dies ist der RSScrawler ' + $scope.version + ' von https://github.com/rix1337/RSScrawler/commits');
            $scope.update = res.data.version.update_ready;
            $scope.docker = res.data.version.docker;
            if ($scope.docker) {
                $(".docker").prop( "disabled", true );
            }
            year = (new Date).getFullYear();
            $("#year").attr("max", year);
            if ($scope.update) {
                $(".versioninfo").append(" - Update verfügbar!");
                console.log('Update steht bereit! Weitere Informationen unter https://github.com/rix1337/RSScrawler/releases/latest');
                showInfo('Update steht bereit! Weitere Informationen unter <a href="https://github.com/rix1337/RSScrawler/releases/latest">github.com</a>.');
            }
            $scope.log = res.data.log;
            $scope.settings = res.data.settings;
            $scope.lists = res.data.lists;
            console.log('Alles abgerufen!');
        }, function (res) {
            console.log('Konnte nichts abrufen!');
            showDanger('Konnte nichts abrufen!');
        });
    }
    
    function getLogOnly() {
        $http.get('api/log/')
        .then(function(res){
            $scope.log = res.data.log;
            console.log('Log abgerufen!');
        }, function (res) {
            console.log('Konnte Log nicht abrufen!');
            showDanger('Konnte Log nicht abrufen!');
        });
    }

    function getSettingsOnly() {
        $http.get('api/settings/')
        .then(function(res){
            $scope.settings = res.data.settings;
            console.log('Einstellungen abgerufen!');
            year = (new Date).getFullYear();
            $("#year").attr("max", year);
        }, function (res) {
            console.log('Konnte Einstellungen nicht abrufen!');
            showDanger('Konnte Einstellungen nicht abrufen!');
        });
    }

    function getListsOnly() {
        $http.get('api/lists/')
        .then(function(res){
            $scope.lists = res.data.lists;
            console.log('Listen abgerufen!');
        }, function (res) {
            console.log('Konnte Listen nicht abrufen!');
            showDanger('Konnte Listen nicht abrufen!');
        });
    }

    function getVersionOnly() {
        $http.get('api/version/')
        .then(function(res){
            $scope.version = res.data.version.ver;
            $(".versioninfo").append(" " + $scope.version);
            console.log('Dies ist der RSScrawler ' + $scope.version + ' von https://github.com/rix1337/RSScrawler/commits');
            $scope.update = res.data.version.update_ready;
            $scope.docker = res.data.version.docker;
            if ($scope.docker) {
                $(".docker").prop( "disabled", true );
            }
            if ($scope.update) {
                console.log('Update steht bereit! Weitere Informationen unter https://github.com/rix1337/RSScrawler/releases/latest');
                showInfo('Update steht bereit! Weitere Informationen unter <a href="https://github.com/rix1337/RSScrawler/releases/latest">github.com</a>.');
            }
            console.log('Version abgerufen!');
        }, function (res) {
            console.log('Konnte Version nicht abrufen!');
            showDanger('Konnte Version nicht abrufen!');
        });
    }

    function setLists() {
        spinLists();
        $http.post('api/lists/', $scope.lists , 'application/json')
        .then(function(res){
            console.log('Listen gespeichert! Änderungen werden im nächsten Suchlauf berücksichtigt.');
            showSuccess('Listen gespeichert! Änderungen werden im nächsten Suchlauf berücksichtigt.');
            getListsOnly();
        }, function (res) {
            console.log('Konnte Listen nicht speichern!');
            showDanger('Konnte Listen nicht speichern!');
        });
    }

    function setSettings() {
        spinSettings();
        $http.post('api/settings/', $scope.settings, 'application/json')
        .then(function(res){
            console.log('Einstellungen gespeichert! Einige Änderungen erfordern einen Neustart.');
            showSuccess('Einstellungen gespeichert! Einige Änderungen erfordern einen Neustart.');
            getSettingsOnly();
        }, function (res) {
            $('#headingTwoOne').addClass('show');
            console.log('Konnte Einstellungen nicht speichern!');
            showDanger('Konnte Einstellungen nicht speichern!');
        });
    }

    function deleteLog() {
        spinLog();
        $http.delete('api/log/')
        .then(function(res){
            console.log('Log geleert!');
            showSuccess('Log geleert!');
            getLogOnly();
        }, function (res) {
            console.log('Konnte Log nicht leeren!');
            showDanger('Konnte Log nicht leeren!');
        });
    }

    $scope.updateLog = function(){
        $timeout(function() {
        getLogOnly();
        $scope.updateLog();
        }, 10000)
    };

    $scope.updateLog();

    function showSuccess(message) {
        $(".alert-success").html(message)
        $(".alert-success").fadeTo(3000, 500).slideUp(500, function(){
            $(".alert-success").slideUp(500);
        });
    }

    function showInfo(message) {
        $(".alert-info").html(message)
        $(".alert-info").fadeTo(10000, 500).slideUp(500, function(){
            $(".alert-info").slideUp(500);
        });
    }

    function showDanger(message) {
        $(".alert-danger").html(message)
        $(".alert-danger").fadeTo(5000, 500).slideUp(500, function(){
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
});
