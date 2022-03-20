let app = angular.module('helperApp', []);

app.controller('helperCtrl', function ($scope, $http, $timeout) {

    $scope.f_blocked = false;
    $scope.sf_hostname = "";
    $scope.ff_hostname = "";

    $scope.to_decrypt = {
        name: false,
        url: false
    };

    $scope.current_to_decrypt = "";

    $scope.wnd_to_decrypt = false;

    $scope.update = function () {
        spinHelper();
        getToDecrypt();
    };

    function spinHelper() {
        $("#spinner-helper").fadeIn().delay(1000).fadeOut();
    }

    function getAntiGate() {
        $.get("http://127.0.0.1:9700/status", function (data) {
            $scope.antigate_available_and_active = data;
        });
    }

    function getToDecrypt() {
        $http.get('./api/to_decrypt/')
            .then(function (res) {
                $scope.to_decrypt = res.data.to_decrypt;
                startToDecrypt()
            }, function (res) {
                console.log('[FeedCrawler Helper] Konnte Pakete zum Entschlüsseln nicht abrufen!');
            });
    }

    function getFBlocked() {
        $http.get('./api/f_blocked/False')
            .then(function (res) {
                $scope.f_blocked = res.data.blocked_sites.sf_ff;
                $scope.sf_hostname = res.data.blocked_sites.sf_hostname;
                $scope.ff_hostname = res.data.blocked_sites.ff_hostname;
                $scope.next_f_run = res.data.blocked_sites.next_f_run;
            }, function (res) {
                console.log('[FeedCrawler Helper] Konnte Block-Status von SF/FF nicht abrufen!');
            });
    }

    function startToDecrypt() {
        if ($scope.to_decrypt.name !== $scope.current_to_decrypt) {
            if ($scope.wnd_to_decrypt) {
                $scope.wnd_to_decrypt.close();
            }
            if ($scope.to_decrypt.name && $scope.to_decrypt.url) {
                $scope.current_to_decrypt = $scope.to_decrypt.name
                if ($scope.f_blocked && $scope.sf_hostname && $scope.to_decrypt.url.includes($scope.sf_hostname)) {
                    console.log('[FeedCrawler Helper] SF ist derzeit geblockt!');
                } else if ($scope.f_blocked && $scope.ff_hostname && $scope.to_decrypt.url.includes($scope.ff_hostname)) {
                    console.log('[FeedCrawler Helper] FF ist derzeit geblockt!');
                } else if ($scope.antigate_available_and_active && $scope.to_decrypt.url.includes("filecrypt.")) {
                    if ($scope.antigate_available_and_active === "false") {
                        let clean_url = $scope.to_decrypt.url;
                        console.log(clean_url)
                        if ($scope.to_decrypt.url.includes("#")) {
                            clean_url = $scope.to_decrypt.url.split('#')[0];
                        }
                        console.log(clean_url)
                        let password = $scope.to_decrypt.password
                        let payload = window.btoa(unescape(encodeURIComponent((clean_url + "|" + password))));
                        $scope.wnd_to_decrypt = window.open("http://127.0.0.1:9700/?payload=" + payload);
                    }
                } else {
                    $scope.wnd_to_decrypt = window.open($scope.to_decrypt.url);
                }
            }
        } else {
            if ($scope.wnd_to_decrypt.closed) {
                $scope.current_to_decrypt = "";
            }
        }
    }

    getAntiGate();
    getFBlocked();
    getToDecrypt();

    $scope.updateToDecrypt = function () {
        $timeout(function () {
            spinHelper();
            getAntiGate();
            getFBlocked();
            getToDecrypt();
            $scope.updateToDecrypt();
        }, 30000)
    };

        $scope.updateToDecrypt();
    }
)
;
