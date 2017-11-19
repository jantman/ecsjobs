FROM python:3.6.3-alpine3.4
# portions based on: https://www.caktusgroup.com/blog/2017/03/14/production-ready-dockerfile-your-python-django-app/
# and on: https://github.com/lesaux/diamond-DockerContainerCollector/blob/master/Dockerfile

# for labeling image at build time
ARG git_commit
ARG git_url
ARG build_time

# Copy in your requirements file
ADD content/requirements.txt /requirements.txt

# Install build deps, then run `pip install`, then remove unneeded build deps all in a single step. Correct the path to your production requirements file, if needed.
RUN set -ex \
    && apk add --no-cache --virtual .build-deps \
            gcc \
            make \
            libc-dev \
            musl-dev \
            linux-headers \
            pcre-dev \
            postgresql-dev \
    && pip install virtualenv \
    && virtualenv /venv \
    && /venv/bin/pip install -U pip \
    && LIBRARY_PATH=/lib:/usr/lib CPATH=/usr/include:/usr/local/include /bin/sh -c "/venv/bin/pip install --no-cache-dir -r /requirements.txt" \
    && runDeps="$( \
            scanelf --needed --nobanner --recursive /venv \
                    | awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
                    | sort -u \
                    | xargs -r apk info --installed \
                    | sort -u \
    )" \
    && apk add --virtual .python-rundeps $runDeps \
    && apk del .build-deps \
    && find /venv/share/diamond/collectors/ -type f -name "*.py" -print0 | xargs -0 sed -i 's|/proc|/host_proc|g'

RUN mkdir -p /etc/diamond/collectors /etc/diamond/handlers /var/log/diamond
ADD content/diamond.conf /etc/diamond/diamond.conf.example
ADD content/config/collectors /etc/diamond/collectors
# Add our modified Diamond modules
ADD content/diskspace.py /venv/share/diamond/collectors/diskspace/diskspace.py
ADD content/snmpraw.py /venv/share/diamond/collectors/snmpraw/snmpraw.py
ADD content/cloudwatch.py /venv/lib/python2.7/site-packages/diamond/handler/cloudwatch.py
RUN mkdir /venv/share/diamond/collectors/lvs
ADD content/lvs.py /venv/share/diamond/collectors/lvs/lvs.py

# configuration and entrypoint
ADD content/config_diamond.py /config_diamond.py
RUN chmod +x /config_diamond.py
ADD content/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# apply the labels
LABEL git_commit=$git_commit git_url=$git_url build_time=$build_time

ENTRYPOINT ["/entrypoint.sh"]
