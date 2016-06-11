var redflareApp = angular.module("redflare", [])

redflareApp.controller("ServerTableCtrl", function($scope, $http, $interval) {
    $scope.getPrivilegeIconURL = function(player) {
        return "privilege-icon/" + player.privilege + "/" + player.color.slice(1, 7) + ".svg"
    }

    var formatTime = function(seconds) {
        if (seconds < 0) {
            return "∞"
        } else {
            var remainingMinutes = Math.floor(seconds / 60)
            var remainingSeconds = Math.floor(seconds % 60)

            return remainingMinutes + ":" + ("00" + remainingSeconds).slice(-2)
        }
    }

    var fetch = function() {
        $scope.loading = 1
        $http.get("api/servers.json").then(function(response) {
            var servers = response.data.servers
            servers.forEach(function(server) {
                server.mutators = server.mutators.join("-")
                server.time_formatted = formatTime(server.time_remaining)
            })
            $scope.servers = servers
            $scope.loading = 0
        })
    }

    $interval(fetch, 10000)
    fetch()

    var countdown = function() {
        if ($scope.servers) {
            $scope.servers.forEach(function(server) {
                if (server.players.length > 0) {
                    server.time_remaining--
                    server.time_formatted = formatTime(server.time_remaining)
                }
            })
        }
    }

    $interval(countdown, 1000)
})
