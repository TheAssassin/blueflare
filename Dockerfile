FROM python:3.7-alpine

MAINTAINER "TheAssassin <theassassin@user.noreply.github.com>"

SHELL ["sh", "-x", "-c"]

RUN apk add --no-cache ca-certificates gcc git musl-dev nodejs libmaxminddb-dev yarn

COPY ./redflare /redflare/redflare
COPY ./frontend /redflare/frontend
COPY ./maps /redflare/maps
COPY ./*.py package.json /redflare/

WORKDIR /redflare/

# ensure installation order, python-geoip-geolite2 installation might fail otherwise
RUN pip3 install python-geoip-python3 python-geoip-geolite2 && \
    python3 setup.py develop && \
    yarn install && \
    adduser -S -D -h /redflare redflare

USER redflare

EXPOSE 3000

CMD python3 webapp.py
