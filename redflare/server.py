import re
import struct


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
        "basic": 1 << 14
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

    def __init__(self, hostname, port, type):
        self.hostname = hostname
        self.port = port
        self.type = type

        # Will be added later as soon as the data is fetched from the server
        # itself
        # see queryreply in src/game/server.cpp

        # integers inside queryreply data
        self.players_count = None
        self.fifteen = None
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

        # players are appended to the queryresponse and thus the last part
        self.players = None

    def parse_query_reply(self, query_reply):
        # Skip first 5 bytes as they are equal to the bytes sent as request
        stream = Cube2BytesStream(query_reply, 5)

        self.players_count = stream.next_int()

        # some constant, whyever they put it there o_O
        self.fifteen = stream.next_int()

        self.protocol = stream.next_int()
        self.game_mode = self.GAMEMODES[stream.next_int()]
        mutators = stream.next_int()
        self.mutators = [k for k, v in self.MUTATORS.items() if v & mutators]
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

        self.map_name = stream.next_string()
        self.description = stream.next_string()

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
        self.players.sort(key=lambda p: p["name"].lower())

        # fallback if the server sends an empty description
        if not self.description.strip():
            self.description = "{}:[{}]".format(self.hostname, self.port)

    @staticmethod
    def from_addserver_line(data):
        parts = data.split()

        hostname = parts[1]
        port = int(parts[2])
        type = int(parts[3])

        return Server(hostname, port, type)

    def to_dict(self):
        return {
            "players_count": self.players_count,
            "fifteen": self.fifteen,
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
            "description": self.description,
            "players": self.players,
        }

    def __repr__(self):
        return "<Server {}:{}>".format(self.hostname, self.port)
