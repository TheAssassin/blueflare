import chardet
import socket
import time
from tornado import gen, iostream, locks
from .server import Server


class MasterClient:
    _cache = None
    _lock = locks.Lock()

    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port

    @gen.coroutine
    def fetch_servers(self):
        def try_cache():
            cache = self.__class__._cache
            # wait 9 seconds before bothering the master server again
            if cache is not None and time.time() - cache["timestamp"] < 9:
                # use exception to return the data to abort the execution of
                # the coroutine without any return statements
                raise gen.Return(cache["data"])

        # return cached value if possible, otherwise refresh the cache
        try_cache()

        with (yield self.__class__._lock.acquire()):
            # second try, the cache might have been filled in the meanwhile
            try_cache()

            # otherwise query the server again
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            stream = iostream.IOStream(sock)
            servers = []

            stream.connect((self.hostname, self.port))

            yield stream.write(b"update\n")
            data = yield stream.read_until_close()

            codec = chardet.detect(data)["encoding"]
            lines = data.decode(codec).splitlines()

            for line in lines:
                if line.startswith("addserver"):
                    server = Server.from_addserver_line(line)
                    servers.append(server)

            stream.close()

            # fill the cache
            self.__class__._cache = {
                "timestamp": time.time(),
                "data": servers,
            }

            return servers
