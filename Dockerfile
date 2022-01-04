FROM python:3-alpine

MAINTAINER "TheAssassin <theassassin@user.noreply.github.com>"

SHELL ["sh", "-x", "-c"]

RUN apk add --no-cache ca-certificates gcc git musl-dev nodejs libmaxminddb-dev yarn libffi-dev

COPY blueflare /blueflare/blueflare
COPY ./frontend /blueflare/frontend
COPY ./maps /blueflare/maps
COPY ./*.py package.json yarn.lock pyproject.toml poetry.lock /blueflare/

WORKDIR /blueflare/

# poetry installs to $HOME, so we have to set that up first
RUN pip install -U poetry && \
    adduser -S -D -h /home/blueflare blueflare && \
    chown -R blueflare /blueflare
USER blueflare

RUN mkdir -p /blueflare && \
    poetry install && \
    yarn install

EXPOSE 3000

CMD poetry run python3 webapp.py
