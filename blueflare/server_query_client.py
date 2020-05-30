import logging
import socket
from tornado import ioloop, gen


class ServerQueryClient:
    _logger = logging.getLogger("blueflare")

    def __init__(self, hostname, port):
        self._hostname = hostname
        self._port = port

        self._ioloop = ioloop.IOLoop.current()

    @gen.coroutine
    def query(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)

        # make sure socket is cleaned up in any case, otherwise we might leak file descriptors
        try:
            sock.connect((self._hostname, self._port + 1))

            # as it's a little easier than fiddling with variables, we'll use a future internally to track the state
            future = gen.Future()

            # this callback will be called once the server receives data
            def handle_input(fd, events):
                if future.done():
                    self._logger.debug("Future already done, ignoring further input")
                    return

                data, source = sock.recvfrom(4096)

                if type(data) != bytes:
                    future.set_exception(RuntimeError("received non-bytes data from socket"))
                else:
                    future.set_result(data)

            # we'll make up to 10 requests before aborting
            request_limit = 10

            self._ioloop.add_handler(sock.fileno(), handle_input, self._ioloop.READ)

            for request_count in range(request_limit):
                self._logger.debug("Send request {} for {}".format(request_count, repr(self)))
                sock.send(b"\x81\xec\x04\x01\x00")

                yield gen.sleep(0.25)

                if future.done():
                    e = future.exception()

                    if e:
                        raise RuntimeError("Exception while trying to read from socket", e)

                    return future.result()

            else:
                self._logger.error("no reply received from {}:{} after {} "
                                  "attempts, aborting...".format(self._hostname, self._port, request_limit))
                future.cancel()

        finally:
            self._ioloop.remove_handler(sock.fileno())
            sock.close()
