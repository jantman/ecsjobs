.. _development:

Development
===========

Any and all contributions are welcome.

.. _development.installing:

Installing for Development
--------------------------

To setup ecsjobs for development:

1. Fork the `ecsjobs <https://github.com/jantman/ecsjobs>`_ repository on GitHub and clone it locally; ``cd ecsjobs``.

2. Create a ``virtualenv`` to run the code in and install it:

.. code-block:: bash

    $ virtualenv venv
    $ source venv/bin/activate
    $ python setup.py develop

3. Check out a new git branch. If you're working on a GitHub issue you opened, your
   branch should be called "issues/N" where N is the issue number.

.. _development.release_checklist:

Release Checklist
-----------------

1. Ensure that Travis tests are passing in all environments.
2. Ensure that test coverage is no less than the last release (ideally, 100%).
3. Build docs for the branch (locally) and ensure they look correct (``tox -e docs``). Commit any changes.
4. Increment the version number in ecsjobs/version.py and add version and release date to CHANGES.rst. ``export ECSJOBS_VER=x.y.z``. Ensure that there are CHANGES.rst entries for all major changes since the last release, and that any new required IAM permissions are explicitly mentioned. Commit changes and push to GitHub. Wait for builds to pass.
5. Confirm that README.rst renders correctly on GitHub.
6. Upload package to testpypi, confirm that README.rst renders correctly.

   * Make sure your ~/.pypirc file is correct (a repo called ``test`` for https://testpypi.python.org/pypi).
   * ``rm -Rf dist``
   * ``python setup.py sdist bdist_wheel``
   * ``twine upload -r test dist/*``
   * Check that the README renders at https://testpypi.python.org/pypi/ecsjobs

7. Tag the release in Git, push tag to GitHub:

   * tag the release with a signed tag: ``git tag -s -a $ECSJOBS_VER -m "$ECSJOBS_VER released $(date +%Y-%m-%d)"``
   * Verify the signature on the tag, just to be sure: ``git tag -v $ECSJOBS_VER``
   * push the tag to GitHub: ``git push origin $ECSJOBS_VER``

8. Upload package to live pypi:

    * ``twine upload dist/*``

9. Run ``./build_docker.sh`` to build the Docker image. Take note of the generated (timestamp) tag.
10. Re-tag the generated Docker image with the version and "latest" and then push to Docker Hub:

   * ``docker tag jantman/ecsjobs:TIMESTAMP jantman/ecsjobs:$ECSJOBS_VER``
   * ``docker push jantman/ecsjobs:$ECSJOBS_VER``
   * ``docker tag jantman/ecsjobs:TIMESTAMP jantman/ecsjobs:latest``
   * ``docker push jantman/ecsjobs:latest``

11. On GitHub, create a release for the tag. Run ``pandoc -f rst -t markdown_github CHANGES.rst`` to convert CHANGES.rst to Markdown, and use the appropriate section for the GitHub release description.
