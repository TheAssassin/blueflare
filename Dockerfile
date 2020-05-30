FROM python:3.7-alpine

MAINTAINER "TheAssassin <theassassin@user.noreply.github.com>"

SHELL ["sh", "-x", "-c"]

RUN apk add --no-cache ca-certificates gcc git musl-dev nodejs libmaxminddb-dev yarn

COPY blueflare /blueflare/blueflare
COPY ./frontend /blueflare/frontend
COPY ./maps /blueflare/maps
COPY ./*.py package.json /blueflare/

WORKDIR /blueflare/

# ensure installation order, python-geoip-geolite2 installation might fail otherwise
RUN pip3 install python-geoip-python3 python-geoip-geolite2 && \
    python3 setup.py develop && \
    yarn install && \
    adduser -S -D -h /blueflare blueflare

USER blueflare

EXPOSE 3000

CMD python3 webapp.py
