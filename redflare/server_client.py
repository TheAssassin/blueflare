import logging
import socket
from tornado import ioloop


class ServerClient:
    logger = logging.getLogger("redflare")

    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port

        self.ioloop = ioloop.IOLoop.current()

        self.timeout = 0.25
        self.timeout_handle = None

        self.request_count = 0

    def fetch_query_reply(self, callback):
        self.callback = callback

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)
        self.sock.connect((self.hostname, self.port+1))

        self.ioloop.add_handler(self.sock.fileno(), self.handle_input,
                                self.ioloop.READ)

        # reset request count
        self.request_count = 0
        self.send_request()

    def send_request(self):
        self.request_count += 1

        limit = 10

        if self.request_count > limit:
            self.logger.error("no reply received from {}:{} after {} "
                              "attempts, aborting...".format(self.hostname,
                                                             self.port,
                                                             limit))

            self.ioloop.remove_handler(self.sock.fileno())

            if self.timeout_handle is not None:
                self.ioloop.remove_timeout(self.timeout_handle)

            self.callback(None)
            self.callback = None

        else:
            self.logger.debug("Send request {} for {}".format(
                self.request_count, repr(self))
            )
            self.sock.send(b"\x81\xec\x04\x01\x00")

            self.timeout_handle = self.ioloop.call_later(self.timeout,
                                                         self.send_request)

    def handle_input(self, fd, events):
        self.ioloop.remove_timeout(self.timeout_handle)

        data, source = self.sock.recvfrom(4096)

        if type(data) != bytes:
            raise RuntimeError

        self.callback(data)
        self.callback = None

        self.sock.close()
