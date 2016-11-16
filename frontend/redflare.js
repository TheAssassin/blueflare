var redflareApp = angular.module("redflare", ["ui.bootstrap"])

var gamemodeMap = {
    "edit": "edit",
    "deathmatch": "dm",
    "capture-the-flag": "ctf",
    "defend-and-control": "dac",
    "bomber-ball": "bb",
    "race": "race",
}

redflareApp.controller("ServerTableCtrl", function($scope, $http, $interval, $sce) {
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
                server.muts_short = []

                server.mutators.forEach(function(mutator) {
                    server.muts_short.push(mutator.slice(0, 2))
                })

                server.mutators = server.mutators.join("-")
                server.muts_short = server.muts_short.join("-")

                server.mode_short = gamemodeMap[server.game_mode]

                server.time_formatted = formatTime(server.time_remaining)

                server.players.forEach(function(player) {
                    var textColor = tinycolor(player.team_color)

                    // replace grey color (or colors with a really low saturation) with black
                    // to improve readability (this includes the default neutral team color)
                    if (textColor.toHsv().s < 0.125) {
                        textColor = tinycolor("#000000")
                    }

                    // darken the color a bit to improve readability
                    player.text_color = textColor.darken(10).toString()
                })
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
                if (server.players.length > 0 && server.time_remaining > 0) {
                    server.time_remaining--
                    server.time_formatted = formatTime(server.time_remaining)
                }
            })
        }
    }

    $interval(countdown, 1000)
})
