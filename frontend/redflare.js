var redflareApp = angular.module("redflare", [])

redflareApp.controller("ServerTableCtrl", function($scope, $http, $interval) {
    $scope.getPrivilegeIconURL = function(player) {
        return "privilege-icon/" + player.privilege + "/" + player.color.slice(1, 7) + ".svg"
    }

    var fetch = function() {
        $scope.loading = 1
        $http.get("api/servers.json").then(function(response) {
            var servers = response.data.servers
            servers.forEach(function(server) {
                server.mutators = server.mutators.join("-")
            })
            $scope.servers = servers
            $scope.loading = 0
        })
    }
    $interval(fetch, 10000)
    fetch()
})
