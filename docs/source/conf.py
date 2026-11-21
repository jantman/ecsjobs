# -*- coding: utf-8 -*-
#
# ecsjobs documentation build configuration file.
#
# Build with:
#   uv run sphinx-build -a -n -W -b html docs/source docs/build/html

import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

# the version is read from the installed package metadata, so ecsjobs must
# be installed (``uv sync``) to build the docs
from ecsjobs.version import VERSION  # noqa: E402

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'

project = u'ecsjobs'
copyright = u'2017 Jason Antman'
author = u'Jason Antman'

version = VERSION
release = version

exclude_patterns = []
pygments_style = 'sphinx'
todo_include_todos = True

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_title = 'v{v} - ECS scheduled job wrapper and reporter'.format(v=version)
html_last_updated_fmt = '%b %d, %Y'

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'boto3': ('https://docs.aws.amazon.com/boto3/latest/', None),
    'docker': ('https://docker-py.readthedocs.io/en/stable/', None),
}

autoclass_content = 'both'
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'private-members': True,
    'show-inheritance': True,
}


def remove_module_docstring(app, what, name, obj, options, lines):
    if what == "module":
        del lines[:]


def setup(app):
    app.connect("autodoc-process-docstring", remove_module_docstring)
