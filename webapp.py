import json
import logging
import os
import re
from tornado import gen, ioloop, web
from blueflare.master_client import MasterClient
from blueflare.privilege_icons import IconNotFoundError, generate_privilege_icon
from blueflare.server_query_client import ServerQueryClient


class ServersAPIHandler(web.RequestHandler):
    logger = logging.getLogger("blueflare")

    @gen.coroutine
    def get(self):
        master_host = os.environ.get("MASTER_HOST", "master.blue-nebula.org")
        master_port = int(os.environ.get("MASTER_PORT", 28800))

        master_client = MasterClient(master_host, master_port)

        self.logger.info("Fetching servers from master server...")
        servers = yield master_client.fetch_servers()

        @gen.coroutine
        def fetch(server):
            server_query_client = ServerQueryClient(server.hostname, server.port)
            try:
                query_reply = yield server_query_client.query()
            except Exception as e:
                print("Error fetching information for %r: %r" % (server, e))
            else:
                if query_reply is not None:
                    server.parse_query_reply(query_reply)

        self.logger.info("Fetching data from {} servers".format(len(servers)))

        y = [fetch(server) for server in servers]
        yield y

        servers_list = [server.to_dict() for server in servers if server.protocol is not None]
        servers_list.sort(key=lambda i: (-i["players_count"], -i["priority"], i["description"].lower()))

        rv = json.dumps(dict(servers=servers_list))

        self.add_header("Content-Type", "application/json")
        self.add_header("Access-Control-Allow-Origin", "*")
        self.write(rv)


class IndexRedirectHandler(web.RequestHandler):
    @gen.coroutine
    def get(self):
        self.redirect("index.html", permanent=False)

    @gen.coroutine
    def head(self):
        return self.get()


class PrivilegeIconHandler(web.RequestHandler):
    def get(self, privilege, color):
        def abort(message):
            self.set_status(400)
            self.add_header("Content-Type", "text/plain")
            self.write(message)

        # validate color format
        if not (len(color) in (3, 6) and re.match("[a-fA-F0-9]+", color)):
            abort("Error: Invalid color")

        else:
            color = "#" + color

            try:
                icon = generate_privilege_icon(privilege, color)
            except IconNotFoundError:
                abort("Error: No such privilege: {}".format(privilege))
            else:
                self.add_header("Content-Type", "image/svg+xml")
                self.write(icon)


class MapScreenshotHandler(web.RequestHandler):
    def get(self, map_name):
        def not_found():
            self.set_status(404)
            self.add_header("Content-Type", "text/plain")
            self.write("No such file or directory")

        this_dir = os.path.abspath(os.path.dirname(__file__))

        if map_name == "unknown":
            unknown_screenshot = os.path.join(this_dir, "blueflare/maps/unknown.png")
            with open(unknown_screenshot, "rb") as f:
                self.add_header("Content-Type", "image/png")
                self.write(f.read())

        else:
            try:
                with open(os.path.join(this_dir, "maps/%s.png" % map_name), "rb") as f:
                    self.add_header("Content-Type", "image/png")
                    self.write(f.read())
            except IOError:
                return not_found()


if __name__ == "__main__":
    # creating web application...
    frontend_path = os.path.join(os.path.dirname(__file__), "frontend")

    application = web.Application([
        (r"/privilege-icon/(\w+)/(\w+).svg", PrivilegeIconHandler),
        (r"/maps/(\w+).png", MapScreenshotHandler),
        (r"/api/servers.json", ServersAPIHandler),
        (r"/?$", IndexRedirectHandler),
        (r"/(.*)", web.StaticFileHandler, {"path": frontend_path}),
    ], autoreload=False)

    # ... listen on port 3000...
    application.listen(3000)

    # ... configure logging...

    # ... set up blueflare logging...
    blueflare_logger = logging.getLogger("blueflare")
    blueflare_logger.setLevel(logging.ERROR)
    blueflare_logger.propagate = False
    blueflare_handler = logging.StreamHandler()
    blueflare_handler.setFormatter(
        logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        )
    )
    blueflare_logger.addHandler(blueflare_handler)

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
