# Redflare, but in Python

This repository provides clients for the [Red Eclipse](http://redeclipse.net) master server
protocol and the server info protocol. It also contains a web application as a frontend and
as an example application.

This application was created as a more modern competitor to the original
[Redflare](https://redflare.ofthings.net) (guess where its name originated from).

This application uses the tornado framework and runs only on Python 3.5.


## Demo

Check out https://redflare.assassinate-you.net/ to watch a demo installation.


## Deployment

The easiest way to deploy this application is to build and run its Docker container.

Just forward the port `3000` to some public port or to some host-local port and use a reverse
proxy like NGINX or Apache2 to forward some domain or route to redflare.
