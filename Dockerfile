FROM python:3.5-alpine

MAINTAINER "TheAssassin <theassassin@user.noreply.github.com>"

RUN apk add --no-cache ca-certificates gcc git musl-dev nodejs && \
    npm install -g bower

ADD ./redflare /redflare/redflare
ADD ./frontend /redflare/frontend
ADD ./*.py ./.bowerrc ./bower.json /redflare/

WORKDIR /redflare/

# ensure installation order, python-geoip-geolite2 installation might fail otherwise
RUN pip3 install python-geoip-python3 python-geoip-geolite2 && \
    python3 setup.py develop && \
    bower --allow-root install && \
    adduser -S -D -h /redflare redflare

USER redflare

EXPOSE 3000

CMD python3 webapp.py
