# template-specialize

![PyPI - Status](https://img.shields.io/pypi/status/template-specialize)
![PyPI](https://img.shields.io/pypi/v/template-specialize)
![GitHub](https://img.shields.io/github/license/craigahobbs/template-specialize)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/template-specialize)

template-specialize is a recursive [Jinja2](https://pypi.org/project/Jinja2/) template
renderer (specializer).


## Links

- [Package on pypi](https://pypi.org/project/template-specialize/)
- [Source code on GitHub](https://github.com/craigahobbs/template-specialize)


## Usage

```
usage: template-specialize [-h] [-c FILE] [-e ENV] [--key KEY] [--value VALUE]
                           [--dump] [-v]
                           [SRC] [DST]

positional arguments:
  SRC            the source template file or directory
  DST            the destination file or directory

options:
  -h, --help     show this help message and exit
  -c FILE        the environment files
  -e ENV         the environment name
  --key KEY      add a template key. Must be paired with a template value.
  --value VALUE  add a template value. Must be paired with a template key.
  --dump         dump the template variables
  -v, --version  show version number and quit
```


## Development

This project is developed using [Python Build](https://github.com/craigahobbs/python-build#readme).
Refer to the Python Build [documentation](https://github.com/craigahobbs/python-build#make-targets)
for development instructions.
