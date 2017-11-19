# private-docker-template

(private) template for Docker image build/test repos

## Testing

Tests should be written for pytest and grouped into ``tests/internal/`` and
``tests/external/``. Internal tests should rely only on [testinfra](http://testinfra.readthedocs.io/en/latest/backends.html#docker)
to test the internals of the containers. External tests should test the public
API of the container, i.e. HTTP requests.

When the tests are run, a ``PYTEST_CONTAINER_ID`` environment variable will be set
to the ID of the (already running) container to test. Wrapper code in [ecsbuild](https://github.com/jantman/ecsbuild/blob/master/ecsbuild/runner.py)
handles starting and stopping the container.

Tests will also have access to import anything in the ecsbuild virtualenv,
including [ecsbuild.test_helpers](https://github.com/jantman/ecsbuild/blob/master/ecsbuild/test_helpers.py)
and any of its [requirements](https://github.com/jantman/ecsbuild/blob/master/setup.py).
