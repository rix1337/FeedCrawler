let app = angular.module('helperApp', []);

app.controller('helperCtrl', function ($scope, $http, $timeout) {

        $scope.to_decrypt = {
            name: false,
            url: false
        };

        $scope.failed = {
            name: false,
            url: false
        };

        $scope.current_to_decrypt = "";
        $scope.current_failed = "";

        $scope.wnd_to_decrypt = false;
        $scope.wnd_failed = false;

        function getToDecrypt() {
            $http.get('./api/to_decrypt/')
                .then(function (res) {
                    $scope.to_decrypt = res.data.to_decrypt;
                    $scope.failed = res.data.failed;
                    console.log('[RSScrawler Helper] Pakete zum Entschlüsseln abgerufen!');
                    startToDecrypt()
                }, function (res) {
                    console.log('[RSScrawler Helper] Konnte Pakete zum Entschlüsseln nicht abgerufen!');
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
            if ($scope.failed.name !== $scope.current_failed) {
                if ($scope.wnd_failed) {
                    $scope.wnd_failed.close();
                }
                if ($scope.failed.name && $scope.failed.url) {
                    $scope.current_failed = $scope.failed.name
                    $scope.wnd_failed = window.open($scope.failed.url);
                }
            }
        }

        getToDecrypt();

        $scope.updateToDecrypt = function () {
            $timeout(function () {
                getToDecrypt();
                $scope.updateToDecrypt();
            }, 60000)
        };

        $scope.updateToDecrypt();
    }
)
;
