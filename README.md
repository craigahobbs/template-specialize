# template-specialize

![PyPI - Status](https://img.shields.io/pypi/status/template-specialize)
![PyPI](https://img.shields.io/pypi/v/template-specialize)
![GitHub](https://img.shields.io/github/license/craigahobbs/template-specialize)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/template-specialize)

**template-specialize** is a command-line tool for rendering
[Jinja2](https://jinja.palletsprojects.com/en/3.0.x/templates/)
templates. It renders individual template files as well as directories of template files.

For example, consider this Markdown name tag template, "nametag.md":

``` jinja2
## Hello, my name is

# {{name}}
{% if title is defined %}
### {{title}}
{% endif %}
```

To render the template file, execute template-specialize as follows. By default, templates are
rendered to the terminal:

```
$ template-specialize nametag.md --key name --value 'John Doe'
## Hello, my name is

# John Doe
```

You can render the template file to an output file:

```
$ template-specialize nametag.md nametag-roy.md --key name --value 'Roy Hobbs' --key title --value 'The best there ever was'
```

You can also render templates contained within one or more directories to an output directory:

```
$ template-specialize templates/ output/ --key var --value value
```


## Links

- [Package on pypi](https://pypi.org/project/template-specialize/)
- [Source code on GitHub](https://github.com/craigahobbs/template-specialize)


## Environment Files

template-specialize was created to "specialize" web service configuration files for different
runtime environments. Environment files are [YAML](https://yaml.org/spec/1.2/spec.html) files that
allow for the definition of inheritable, structured template configuration values. Consider the
following environments file:

``` yaml
base:
  values:
    service_name: my-service

test_base:
  parents: [base]
  values:
     db_host: test-db-host

test:
  parents: [test_base]
  values:
     db_name: test-db

live:
  parents: [base]
  values:
     db_host: live-db-host
     db_name: live-db
```

To render a template file using an environment, specify the environment file (or files) and the
environment name with which to render the template:

```
$ template-specialize config-template.yaml config.yaml -c environments.yaml -e test
```

To view the template configuration data use the "--dump" argument:

```
$ template-specialize -c environments.yaml -e test --dump
db_host: test-db-host
db_name: test-db
service_name: my-service
```


## AWS Parameter Store

template-specialize can retrieve template values from
[AWS Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html)
using
[botocore](https://pypi.org/project/botocore/).

Here's an example of a YAML configuration file with a Parameter Store secret:

``` jinja2
my_secret: {% filter tojson %}{% aws_parameter_store 'parameter-name' %}{% endfilter %}
```

botocore is usually configured using
[environment variables](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#using-environment-variables).


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
