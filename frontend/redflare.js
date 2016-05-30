var redflareApp = angular.module("redflare", [])

redflareApp.controller("ServerTableCtrl", function($scope, $http, $interval) {
    var fetch = function() {
        $scope.loading = 1
        $http.get("api/servers.json").then(function(response) {
            var servers = response.data.servers
            for (var i = 0; i < servers.length; i++) {
                var server = servers[i]
                server.mutators = server.mutators.join("-")
                server.players.sort(function(a, b) {
                    return a.name.toLowerCase() > b.name.toLowerCase()
                })
            }
            $scope.servers = servers
            $scope.loading = 0
        })
    }
    $interval(fetch, 10000)
    fetch()
})
