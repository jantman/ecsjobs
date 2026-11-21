.. _development:

Development
===========

Any and all contributions are welcome.

.. _development.installing:

Installing for Development
--------------------------

ecsjobs supports Python 3.8 through 3.14 and uses `uv <https://docs.astral.sh/uv/>`_ to manage its environment.

1. Fork the `ecsjobs <https://github.com/jantman/ecsjobs>`_ repository on GitHub and clone it locally; ``cd ecsjobs``.

2. Install the package and all dependency groups into ``.venv/``:

.. code-block:: bash

    uv sync --locked --all-groups

3. Check out a new git branch. If you're working on a GitHub issue you opened, your
   branch should be called "issues/N" where N is the issue number.

.. _development.testing:

Tests, Lint and Docs
--------------------

All of these are run in CI by ``.github/workflows/tests.yml``. The tests run on every supported Python version with the locked dependencies, and on the oldest supported Python with the lowest dependency versions that ``pyproject.toml`` allows (``uv pip install --resolution lowest-direct -e .`` and then ``uv pip install --group dev``, in a fresh virtualenv).

* Lint: ``uv run ruff check``
* Tests: ``uv run pytest``. Test coverage must stay at 100% (this is enforced). To run a single test, use ``uv run pytest ecsjobs/tests/test_config.py::TestClass::test_name``.
* Docs: ``uv run sphinx-build -a -n -W -b html docs/source docs/build/html``. Warnings are treated as errors. The package must be installed (as above), as the docs read the version from its metadata.
* Docker image smoke test: ``docker build -t ecsjobs:dev .`` and then ``dev/docker_smoke_test.sh ecsjobs:dev``. This runs the image end-to-end in a container against a mocked AWS (moto).

Documentation for behavior changes must be updated in ``docs/source`` along with the code.

.. _development.releasing:

Releasing
---------

The version number lives only in ``pyproject.toml``. To release:

1. Increment ``version`` in ``pyproject.toml`` and run ``uv lock``.
2. Merge the change to ``master``.

When a push to ``master`` has a version greater than the latest GitHub release, ``.github/workflows/release.yml`` runs the tests, publishes the package to PyPI (using PyPI trusted publishing), pushes the Docker image to ``ghcr.io/jantman/ecsjobs`` as ``<version>`` and ``latest``, and creates the Git tag (the bare version, e.g. ``2.0.0``) and a GitHub release with automatically generated release notes. Do not create tags manually. There is no changelog file; release notes are the `GitHub releases <https://github.com/jantman/ecsjobs/releases>`_.

The documentation is built and deployed to GitHub Pages at https://jantman.github.io/ecsjobs/ by ``.github/workflows/docs.yml`` on every push to ``master``.
