template-specialize
===================

.. |badge-status| image:: https://img.shields.io/pypi/status/template-specialize?style=for-the-badge
   :alt: PyPI - Status
   :target: https://pypi.python.org/pypi/template-specialize/

.. |badge-version| image:: https://img.shields.io/pypi/v/template-specialize?style=for-the-badge
   :alt: PyPI
   :target: https://pypi.python.org/pypi/template-specialize/

.. |badge-travis| image:: https://img.shields.io/travis/craigahobbs/template-specialize?style=for-the-badge
   :alt: Travis (.org)
   :target: https://travis-ci.org/craigahobbs/template-specialize

.. |badge-codecov| image:: https://img.shields.io/codecov/c/github/craigahobbs/template-specialize?style=for-the-badge
   :alt: Codecov
   :target: https://codecov.io/gh/craigahobbs/template-specialize

.. |badge-license| image:: https://img.shields.io/github/license/craigahobbs/template-specialize?style=for-the-badge
   :alt: GitHub
   :target: https://github.com/craigahobbs/template-specialize/blob/master/LICENSE

.. |badge-python| image:: https://img.shields.io/pypi/pyversions/template-specialize?style=for-the-badge
   :alt: PyPI - Python Version
   :target: https://www.python.org/downloads/

|badge-status| |badge-version|

|badge-travis| |badge-codecov|

|badge-license| |badge-python|

template-specialize is a recursive `Jinja2 <http://jinja.pocoo.org/docs/2.10/templates/>`__ template renderer
(specializer).


Usage
-----

::

   usage: template-specialize [-h] [-c FILE] [-e ENV] [--key KEY] [--value VALUE]
                              [--dump] [-v]
                              [SRC] [DST]

   positional arguments:
     SRC            the source template file or directory
     DST            the destination file or directory

   optional arguments:
     -h, --help     show this help message and exit
     -c FILE        the environment files
     -e ENV         the environment name
     --key KEY      add a template key. Must be paired with a template value.
     --value VALUE  add a template value. Must be paired with a template key.
     --dump         dump the template variables
     -v, --version  show version number and quit
