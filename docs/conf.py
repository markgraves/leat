# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
sys.path.insert(0, os.path.abspath('..'))

version = "0.5.0"

source_suffix = ['.rst', '.md']

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'leat'
copyright = '2023, Mark Graves'
author = 'Mark Graves'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["myst_parser", "sphinx.ext.autodoc", "sphinx.ext.coverage"]

extensions.append("sphinx.ext.napoleon")
extensions.append("autoapi.extension")

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

napoleon_google_docstring = True
#napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True

autoapi_type = 'python'
autoapi_dirs = ['../leat']
autoapi_generate_api_docs = True

autosummary_imported_members = False

# Can't get __init__ to generate. Tried the following:

# napoleon_include_init_with_doc = True

# autoclass_content = 'both'

# autodoc_default_options = {
#     'special-members': '__init__',
#     'undoc-members': True,
#     }

# import inspect

# def skip_init_without_args(app, what, name, obj, would_skip, options):
#     if name == '__init__':
#         func = getattr(obj, '__init__')
#         spec = inspect.getfullargspec(func)
#         return not spec.args and not spec.varargs and not spec.varkw and not spec.kwonlyargs
#     return would_skip

# def setup(app):
#     app.connect("autodoc-skip-member", skip_init_without_args)


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
