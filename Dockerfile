FROM python:3.6.3-alpine3.4
MAINTAINER jason@jasonantman.com

# for labeling image at build time
ARG git_commit
ARG git_url
ARG build_time
ARG whlname

ADD dist/$whlname /tmp/

RUN pip install -U pip \
  && mkdir -p /root/.aws \
  && pip install /tmp/$whlname \
  && which ecsjobs \
  && pip freeze

# apply the labels
LABEL git_commit=$git_commit git_url=$git_url build_time=$build_time maintainer="jason@jasonantman.com"

ENTRYPOINT ["/usr/local/bin/ecsjobs"]
