let app = angular.module('helperApp', []);

app.controller('helperCtrl', function ($scope, $http, $timeout) {

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

        function getToDecrypt() {
            $http.get('./api/to_decrypt/')
                .then(function (res) {
                    $scope.to_decrypt = res.data.to_decrypt;
                    startToDecrypt()
                }, function (res) {
                    console.log('[FeedCrawler Helper] Konnte Pakete zum Entschlüsseln nicht abrufen!');
                });
        }

        function startToDecrypt() {
            if ($scope.to_decrypt.name !== $scope.current_to_decrypt) {
                if ($scope.wnd_to_decrypt) {
                    $scope.wnd_to_decrypt.close();
                }
                if ($scope.to_decrypt.name && $scope.to_decrypt.url) {
                    $scope.current_to_decrypt = $scope.to_decrypt.name
                    $scope.wnd_to_decrypt = window.open($scope.to_decrypt.url);
                }
            }
        }

        getToDecrypt();

        $scope.updateToDecrypt = function () {
            $timeout(function () {
                spinHelper();
                getToDecrypt();
                $scope.updateToDecrypt();
            }, 60000)
        };

        $scope.updateToDecrypt();

        $scope.cleanRam = function () {
            $timeout(function () {
                window.close();
            }, 3600000)
        };

        $scope.cleanRam();
    }
)
;
