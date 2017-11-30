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
