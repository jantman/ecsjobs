Running
=======

Locally via Docker
------------------

To pull the Docker image

    docker pull jantman/ecsjobs:latest

To run locally via Docker to validate a configuration directory ``./conf``:

    docker run -it --rm \
      -e ECSJOBS_LOCAL_CONF_PATH=/tmp/conf \
      -v $(pwd)/conf:/tmp/conf \
      jantman/ecsjobs:latest \
      validate

To run the "foo" schedule locally in a detached/background container (i.e. as a cron job) and allow it to run Docker execs, assuming your Docker socket is at ``/var/run/docker.sock``, your configuration directory is at ``./conf``, and you want to use AWS credentials from ``~/.aws/credentials``:

    docker run --rm -d \
      -e ECSJOBS_LOCAL_CONF_PATH=/tmp/conf \
      -e DOCKER_HOST=unix:///tmp/docker.sock \
      -v $(pwd)/conf:/tmp/conf \
      -v /var/run/docker.sock:/tmp/docker.sock \
      -v $(readlink -f ~/.aws/credentials):/root/.aws/credentials \
      jantman/ecsjobs:latest \
      run foo

Note that when running in this method, the ``LocalCommand`` class runs commands inside the ecsjobs Docker container, not on the host system.

Locally via pip
---------------

To run locally directly on the host OS, i.e. so the ``LocalCommand`` class will run commands on the host, first setup a virtualenv and install ecsjobs:

    virtualenv --python=python3.6 .
    source bin/activate
    pip install ecsjobs

To run the "foo" schedule locally using a configuration directory at ``./conf``:

    ECSJOBS_LOCAL_CONF_PATH=$(readlink -f ./conf) ecsjobs run foo

In ECS
------

Note that because of how ECS Scheduled Tasks work, you'll need to create a separate Task Definition for
each schedule that you want ecsjobs to run. As an example, if your jobs have two different ``schedule``
values, "daily" and "weekly", you'd need to create two separate ECS Task Definitions that differ only
by the command they run (``run daily`` and ``run weekly``, respectively).
