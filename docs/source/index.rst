.. meta::
   :description: A scheduled job wrapper for ECS, focused on email reporting and adding docker exec and local command abilities.

.. include:: ../../README.rst

Upgrading to 2.0
================

* The package requires Python 3.8 or newer and is tested on Python 3.8 through 3.14. The Docker image is built on Python 3.14 (see below).
* The Docker image is now published only to the GitHub Container Registry as ``ghcr.io/jantman/ecsjobs`` (tags ``<version>`` and ``latest``); the ``jantman/ecsjobs`` image on Docker Hub is no longer updated. The image is built on current Alpine and Python 3.14 (previously 3.9), which matters for any Python scripts your jobs run inside it.
* The AWS CLI in the Docker image is now version 2 (Alpine's ``aws-cli`` package) instead of version 1. Check job scripts for commands that changed between the two, such as the removed ``aws ecr get-login`` and the new default output pager and binary format.
* The Docker image's ``git_commit``, ``git_url``, ``build_time`` and ``maintainer`` labels are replaced by standard ``org.opencontainers.image.*`` labels.
* The ``command`` array of ``LocalCommand``, ``DockerExec`` and ``EcsDockerExec`` jobs is now validated so that *every* element must be a string; previously only the first element was checked.
* Configuration YAML is loaded with ``yaml.safe_load``.
* Unknown keys in the ``global`` section or in a job now fail validation; previously they were silently ignored. Check your configuration (for example, for misspelled option names) before upgrading.
* A ``failure_command`` with arguments now works; previously any command with arguments raised an error.

Contents
=========

.. toctree::
   :maxdepth: 4

   Configuration <configuration>
   Running <running>
   API <modules>
   Development <development>

Release Notes
=============

Release notes for each version are published as `GitHub releases <https://github.com/jantman/ecsjobs/releases>`_.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
