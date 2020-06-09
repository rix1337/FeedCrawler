let app = angular.module('helperApp', []);

app.controller('helperCtrl', function ($scope, $http, $timeout) {

        $scope.to_solve = {
            name: false,
            url: false
        };

        $scope.current = "";

        function getToSolve() {
            $http.get('../api/to_solve/')
                .then(function (res) {
                    $scope.to_solve = res.data;
                    console.log('[RSScrawler Helper] Paket zum Entschlüsseln abgerufen!');
                    startToSolve()
                }, function (res) {
                    console.log('[RSScrawler Helper] Konnte Paket zum Entschlüsseln nicht abgerufen!');
                });
        }

        function startToSolve() {
            if ($scope.to_solve.name !== $scope.current) {
                if ($scope.to_solve.name && $scope.to_solve.url) {
                    $scope.current = $scope.to_solve.name
                    window.open($scope.to_solve.url);
                }
            }
        }

        getToSolve();

        $scope.updateToSolve = function () {
            $timeout(function () {
                getToSolve();
                $scope.updateToSolve();
            }, 60000)
        };

        $scope.updateToSolve();
    }
)
;
