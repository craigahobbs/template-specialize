# template-specialize

![PyPI - Status](https://img.shields.io/pypi/status/template-specialize)
![PyPI](https://img.shields.io/pypi/v/template-specialize)
![GitHub](https://img.shields.io/github/license/craigahobbs/template-specialize)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/template-specialize)

**template-specialize** is a command-line tool for rendering
[Jinja2](https://pypi.org/project/Jinja2/)
templates. It renders individual template files as well as directories of template files.

For example, consider this [Markdown](https://guides.github.com/features/mastering-markdown/) name
tag template, "nametag.md":

``` jinja2
## Hello, my name is

# {{name}}
{% if title is defined %}
### {{title}}
{% endif %}
```

Use template-specialize to render the template. By default, templates are rendered to the terminal:

```
$ template-specialize ~/tmp/nametag.md --key name --value 'John Doe'
## Hello, my name is

# John Doe
```

You can render the template any number of times:

```
$ template-specialize ~/tmp/nametag.md --key name --value 'Roy Hobbs' --key title --value 'The best there ever was'
## Hello, my name is

# Roy Hobbs

### The best there ever was
```


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
