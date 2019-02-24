[![Build Status](https://travis-ci.org/craigahobbs/template-specialize.svg?branch=master)](https://travis-ci.org/craigahobbs/template-specialize)
[![Code Coverage](https://codecov.io/gh/craigahobbs/template-specialize/branch/master/graph/badge.svg)](https://codecov.io/gh/craigahobbs/template-specialize)
[![Version](https://img.shields.io/pypi/v/template-specialize.svg)](https://pypi.org/project/template-specialize/)

template-specialize is a recursive [Jinja2](http://jinja.pocoo.org/docs/2.10/templates/) template renderer (specializer).

##  Usage

```
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
```
