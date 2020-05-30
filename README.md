# Blueflare

This repository provides clients for the [Blue Nebula](https://github.com/blue-nebula) master server
protocol and the server info protocol. It also contains a web application as a frontend and
as an example application.

This application was created as an alternative to the original
[Redflare](http://redflare.ofthings.net)
([Github project](https://github.com/stainsby/redflare), guess what its name was inspired by),
written in Python 3 using standard components like Bootstrap 3.

This application uses the tornado framework and runs only on Python 3.5.


## Demo

Check out https://blueflare.assassinate-you.net/, the official instance.


## Deployment

The easiest way to deploy this application is to build and run its Docker container.

Just forward the port `3000` to some public port or to some host-local port and use a reverse
proxy like NGINX or Apache2 to forward some domain or route to this application.

If you decide to use the reverse proxy workflow, you can also just use the
[docker-compose](https://docs.docker.com/compose/) configuration that is included in this
repository. After cloning the repository and
[installing docker-compose](https://docs.docker.com/compose/install/), run the following command
to build the image and create and start your container:

```
docker-compose up
```

Then you can set up a reverse proxy for `127.0.0.1:3000`. You may also need a rewrite rule that
rewrites the root route (`/`) to `/index.html`.

An NGINX site configuration could look like this:

```
server {
    listen 80;
    listen [::]80;

    server_name <insert your hostname here>;

    rewrite ^/$ /index.html;

    location / {
            proxy_pass http://127.0.0.1:3000;
    }

    // ...
    // logging configuration etc.
}

```
