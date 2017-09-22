import glob
import os
import re
import shlex
import struct

from geoip2.database import Reader as GeoIPReader
from geoip2.errors import AddressNotFoundError


# assumes to find a GeoLite2 database in the current working directory
geoip_reader = GeoIPReader(glob.glob("GeoLite2-*.mmdb")[0])


class Cube2BytesStream:

    # copied from src/shared/cube2font.c
    CUBE2UNICHARS = [
        0, 192, 193, 194, 195, 196, 197, 198, 199, 9, 10, 11, 12, 13, 200,
        201, 202, 203, 204, 205, 206, 207, 209, 210, 211, 212, 213, 214, 216,
        217, 218, 219, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45,
        46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62,
        63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79,
        80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96,
        97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110,
        111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124,
        125, 126, 220, 221, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232,
        234, 235, 236, 237, 238, 239, 241, 242, 243, 244, 245, 246, 233, 248,
        249, 250, 251, 252, 253, 255, 0x104, 0x105, 0x106, 0x107, 0x10C,
        0x10D, 0x10E, 0x10F, 0x118, 0x119, 0x11A, 0x11B, 0x11E, 0x11F, 0x130,
        0x131, 0x141, 0x142, 0x143, 0x144, 0x147, 0x148, 0x150, 0x151, 0x152,
        0x153, 0x158, 0x159, 0x15A, 0x15B, 0x15E, 0x15F, 0x160, 0x161, 0x164,
        0x165, 0x16E, 0x16F, 0x170, 0x171, 0x178, 0x179, 0x17A, 0x17B, 0x17C,
        0x17D, 0x17E, 0x404, 0x411, 0x413, 0x414, 0x416, 0x417, 0x418, 0x419,
        0x41B, 0x41F, 0x423, 0x424, 0x426, 0x427, 0x428, 0x429, 0x42A, 0x42B,
        0x42C, 0x42D, 0x42E, 0x42F, 0x431, 0x432, 0x433, 0x434, 0x436, 0x437,
        0x438, 0x439, 0x43A, 0x43B, 0x43C, 0x43D, 0x43F, 0x442, 0x444, 0x446,
        0x447, 0x448, 0x449, 0x44A, 0x44B, 0x44C, 0x44D, 0x44E, 0x44F, 0x454,
        0x490, 0x491
    ]

    def __init__(self, data, offset):
        self.data = data
        self.offset = offset

    # see getint in src/shared/tools.cpp
    def next_int(self):
        next_int = struct.unpack(b"<b", self.data[self.offset:self.offset+1])[0]
        if next_int == -128:
            next_int = struct.unpack("<h", self.data[self.offset+1:self.offset+3])[0]
            self.offset += 3
        elif next_int == -127:
            next_int = struct.unpack("<i", self.data[self.offset+1:self.offset+5])[0]
            self.offset += 5
        else:
            self.offset += 1
        return next_int

    # see getstring in src/shared/tools.cpp
    def next_string(self):
        rv = []

        def getchar():
            return struct.unpack(b"<B", self.data[self.offset:self.offset+1])[0]

        char = getchar()

        while char != 0 and len(self.data) > 0:
            rv.append(chr(self.CUBE2UNICHARS[char]))
            self.offset += 1
            char = getchar()

        self.offset += 1

        return "".join(rv)


class Server:
    # see src/game/gamemode.h
    MUTATORS = {
        "multi": 1 << 0,
        "ffa": 1 << 1,
        "coop": 1 << 2,
        "insta": 1 << 3,
        "medieval": 1 << 4,
        "kaboom": 1 << 5,
        "duel": 1 << 6,
        "survivor": 1 << 7,
        "classic": 1 << 8,
        "onslaught": 1 << 9,
        "freestyle": 1 << 10,
        "vampire": 1 << 11,
        "resize": 1 << 12,
        "hard": 1 << 13,
        "basic": 1 << 14,
        # game specific mutators
        "gsp1": 1 << 15,
        "gsp2": 1 << 16,
        "gsp3": 1 << 17,
    }

    # more descriptive than "gsp1", "gsp2" or "gsp3"
    GSP_MUTATORS = {
        "deathmatch": ["gladiator", "oldschool"],
        "capture-the-flag": ["quick", "defend", "protect"],
        "defend-and-control": ["quick", "king"],
        "bomber-ball": ["hold", "basket", "attack"],
        "race": ["timed", "endurance", "gauntlet"],
    }

    # see src/game/game.h
    MASTERMODES = [
        "open",
        "veto",
        "locked",
        "private",
        "password",
    ]

    # see src/game/gamemode.h
    GAMEMODES = [
        "demo",
        "edit",
        "deathmatch",
        "capture-the-flag",
        "defend-and-control",
        "bomber-ball",
        "race",
    ]

    def __init__(self, ip_address, port, priority, flags):
        self.hostname = ip_address
        self.port = port
        self.priority = priority
        self.flags = flags

        try:
            self.country = geoip_reader.country(ip_address).country.iso_code
        except (AttributeError, AddressNotFoundError):
            self.country = None

        # Will be added later as soon as the data is fetched from the server
        # itself
        # see queryreply in src/game/server.cpp

        # integers inside queryreply data
        self.players_count = None
        self.number_of_ints = None
        self.protocol = None
        self.game_mode = None
        self.mutators = None
        self.time_remaining = None
        self.max_slots = None
        self.mastermode = None
        self.number_of_game_vars = None
        self.modification_percentage = None
        self.version = (None, None, None)
        self.version_platform = None
        self.version_arch = None
        self.game_state = None
        self.time_left = None

        # strings inside queryreply data
        self.map_name = None
        self.description = None
        self.versionbranch = None

        # players are appended to the queryresponse and thus the last part
        self.players = None

    def parse_query_reply(self, query_reply):
        # Skip first 5 bytes as they are equal to the bytes sent as request
        stream = Cube2BytesStream(query_reply, 5)

        self.players_count = stream.next_int()

        # the number of integers following this value
        # after this, the map name string etc. will follow
        self.number_of_ints = stream.next_int()

        self.protocol = stream.next_int()
        self.game_mode = self.GAMEMODES[stream.next_int()]

        mutators = stream.next_int()
        self.mutators = [k for k, v in self.MUTATORS.items() if v & mutators]
        for i, gsp in enumerate(["gsp1", "gsp2", "gsp3"]):
            if gsp in self.mutators:
                gsp_description = self.GSP_MUTATORS[self.game_mode][i]
                self.mutators[self.mutators.index(gsp)] = gsp_description

        self.time_remaining = stream.next_int()
        self.max_slots = stream.next_int()
        self.mastermode = self.MASTERMODES[stream.next_int()]
        self.modification_percentage = stream.next_int()
        self.number_of_game_vars = stream.next_int()
        self.version = (stream.next_int(),
                        stream.next_int(),
                        stream.next_int())
        self.version_platform = stream.next_int()
        self.version_arch = stream.next_int()
        self.game_state = stream.next_int()
        self.time_left = stream.next_int()

        # 15 values fetched
        # make sure there're no ints left to be fetched before interpreting
        # the following bytes as map name strings
        # TODO: notify in those cases so that the application is updated on
        # protocol updates
        for i in range(15, self.number_of_ints):
            # throw away value
            stream.next_int()

        self.map_name = stream.next_string()

        this_dir = os.path.abspath(os.path.dirname(__file__))
        screenshot_name = "%s.png" % self.map_name
        screenshot_path = os.path.join(this_dir, "../maps/%s" % screenshot_name)
        if os.path.isfile(screenshot_path):
            self.map_screenshot = screenshot_name
        else:
            self.map_screenshot = "unknown.png"

        self.description = stream.next_string()

        # from 1.5.5 on, the server sends a versionbranch string which has to
        # be parsed
        if self.version[:2] == (1, 5) and self.version[2] > 3:
            self.versionbranch = stream.next_string()

        self.players = []

        for i in range(self.players_count):
            player = stream.next_string()
            parts = player.split("\f")
            team_color, name = re.match("\[([0-9]+)\](.*)", parts[4]).groups()

            self.players.append({
                "color": "#" + hex(int(parts[2].strip("[]")))[2:].zfill(6),
                "privilege": parts[3].strip("($)")[4:-3],
                "team_color": "#" + hex(int(team_color))[2:].zfill(6),
                "name": name,
            })

        for player in self.players:
            account = stream.next_string().strip()

            if len(account) == 0:
                account = None

            player["account"] = account

        self.players.sort(key=lambda p: p["name"].lower())

        # fallback if the server sends an empty description
        if not self.description.strip():
            self.description = "{}:[{}]".format(self.hostname, self.port)

        # limit server description to 80 chars
        # https://github.com/red-eclipse/base/compare/0512024fef0f...01f6afe516d8
        self.description = self.description[:80]

    @staticmethod
    def from_addserver_line(data):
        parts = shlex.split(data)

        hostname = parts[1]
        port = int(parts[2])
        priority = int(parts[3])
        flags = list(parts[-2])

        return Server(hostname, port, priority, flags)

    def to_dict(self):
        return {
            "hostname": self.hostname,
            "port": self.port,
            "priority": self.priority,
            "flags": self.flags,
            "country": self.country,
            "players_count": self.players_count,
            "protocol": self.protocol,
            "game_mode": self.game_mode,
            "mutators": self.mutators,
            "time_remaining": self.time_remaining,
            "max_slots": self.max_slots,
            "mastermode": self.mastermode,
            "modification_percentage": self.modification_percentage,
            "number_of_game_vars": self.number_of_game_vars,
            "version": ".".join((str(v) for v in self.version)),
            "version_platform": self.version_platform,
            "version_arch": self.version_arch,
            "game_state": self.game_state,
            "time_left": self.time_left,
            "map_name": self.map_name,
            "map_screenshot": self.map_screenshot,
            "description": self.description,
            "players": self.players,
        }

    def __repr__(self):
        return "<Server {}:{}>".format(self.hostname, self.port)
