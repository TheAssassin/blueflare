FROM alpine:3.3

MAINTAINER "TheAssassin <theassassin@user.noreply.github.com>"

RUN apk add --no-cache ca-certificates gcc git musl-dev nodejs python3 python3-dev && \
    python3 -m ensurepip && \
    npm install -g bower

ADD ./redflare /redflare/redflare
ADD ./frontend /redflare/frontend
ADD ./*.py ./.bowerrc ./bower.json /redflare/

WORKDIR /redflare/

RUN python3 setup.py develop && \
    bower --allow-root install && \
    adduser -S -D -h /redflare redflare

USER redflare

EXPOSE 3000

CMD python3 webapp.py
