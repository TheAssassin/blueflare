import json
import logging
import os
from tornado import gen, ioloop, web
from redflare.master_client import MasterClient
from redflare.server_client import ServerClient


class IndexHandler(web.RequestHandler):
    logger = logging.getLogger("redflare")

    @gen.coroutine
    def get(self):
        master_client = MasterClient("play.redeclipse.net", 28800)

        self.logger.info("Fetching servers from master server...")
        servers = yield master_client.fetch_servers()

        @gen.coroutine
        def fetch(server):
            server_client = ServerClient(server.hostname, server.port)
            query_reply = yield gen.Task(server_client.fetch_query_reply)
            if query_reply is not None:
                server.parse_query_reply(query_reply)


        self.logger.info("Fetching data from {} servers".format(len(servers)))
        y = [fetch(server) for server in servers]
        yield y

        servers_list = [server.to_dict() for server in servers if server.protocol is not None]
        servers_list.sort(key=lambda i: (-i["players_count"], i["description"].lower()))

        rv = json.dumps(dict(servers=servers_list))

        self.add_header("Content-Type", "application/json")
        self.add_header("Access-Control-Allow-Origin", "*")
        self.write(rv)


if __name__ == "__main__":
    # creating web application...
    frontend_path = os.path.join(os.path.dirname(__file__), "frontend")

    application = web.Application([
        (r"/api/servers.json", IndexHandler),
        (r"/(.*)", web.StaticFileHandler, {"path": frontend_path})
    ], autoreload=False)

    # ... listen on port 3000...
    application.listen(3000)

    # ... configure logging...

    # ... set up redflare logging...
    redflare_logger = logging.getLogger("redflare")
    redflare_logger.setLevel(logging.ERROR)
    redflare_logger.propagate = False
    redflare_handler = logging.StreamHandler()
    redflare_handler.setFormatter(
        logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]')
    )
    redflare_logger.addHandler(redflare_handler)

    # ... and enable tornado web logs properly...
    tornado_logger = logging.getLogger("tornado.access")
    tornado_logger.setLevel(logging.INFO)
    tornado_logger.propagate = False
    tornado_handler = logging.StreamHandler()
    tornado_handler.setFormatter(
        logging.Formatter("%(asctime)s: %(message)s")
    )
    tornado_logger.addHandler(tornado_handler)

    # ... and finally run the application
    ioloop.IOLoop.current().start()
