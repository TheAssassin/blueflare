import socket
from tornado import gen, iostream
from .server import Server


class MasterClient:
    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port

    @gen.coroutine
    def fetch_servers(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        stream = iostream.IOStream(sock)
        servers = []

        stream.connect((self.hostname, self.port))

        yield stream.write(b"update\n")
        data = yield stream.read_until_close()

        lines = data.decode().splitlines()

        for line in lines:
            if line.startswith("addserver"):
                server = Server.from_addserver_line(line)
                servers.append(server)

        stream.close()
        return servers
