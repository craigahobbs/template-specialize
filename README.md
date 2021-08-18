# template-specialize

[![PyPI - Status](https://img.shields.io/pypi/status/template-specialize)](https://pypi.org/project/template-specialize/)
[![PyPI](https://img.shields.io/pypi/v/template-specialize)](https://pypi.org/project/template-specialize/)
[![GitHub](https://img.shields.io/github/license/craigahobbs/template-specialize)](https://github.com/craigahobbs/template-specialize/blob/main/LICENSE)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/template-specialize)](https://pypi.org/project/template-specialize/)

**template-specialize** is a command-line tool for rendering
[Jinja2](https://jinja.palletsprojects.com/en/3.0.x/templates/)
templates.

For example, consider this Markdown name tag template, "nametag.md":

``` jinja2
## Hello, my name is

# {{name}}
{% if title is defined %}
### {{title}}
{% endif %}
```

To render the template, execute template-specialize as follows:

```
$ template-specialize nametag.md nametag-roy.md -k name 'Roy Hobbs' -k title 'The best there ever was'
```

Afterward, the output file contains the rendered template:

```
## Hello, my name is

# Roy Hobbs

### The best there ever was
```

You can also render directories of templates to an output directory:

```
$ template-specialize template/ output/ -k name value
```


## Environment Files

template-specialize was originally created to "specialize" web service configuration files for different runtime
environments. Environment files are [YAML](https://yaml.org/spec/1.2/spec.html) files that allow for the definition of
inheritable, structured template configuration values. Consider the following environments file:

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

To render a template file using an environment, specify the environment file (or files) and the environment name with
which to render the template:

```
$ template-specialize config-template.yaml config.yaml -c environments.yaml -e test
```

To view the template configuration data use the "--dump" argument:

```
$ template-specialize config-template.yaml config.yaml -c environments.yaml -e test --dump
db_host: test-db-host
db_name: test-db
service_name: my-service
```


## Renaming and Deleting Output Files

When specializing a template directory, it is sometimes necessary to rename an output file or directory. For example,
consider a Python project template with the following structure:

```
.
|-- README.md
|-- package-name.txt
|-- setup.py
`-- src
    |-- __init__.py
    |-- package_name
    |   |-- __init__.py
    |   `-- package_name.py
    `-- tests
        |-- __init__.py
        `-- test_package_name.py
```

As part of the specialization, we'd like to rename the "package_name" directory, the "package_name.py" file, and the
"test_package_name.py" file to the specialized package name. To accomplish this, we add the "package-name.txt' utility
file and call the "template_specialize_rename" Jinja2 extension:

``` jinja2
{# Rename template files #}
{% template_specialize_rename 'src/tests/test_package_name.py', 'test_' + package_name + '.py' %}
{% template_specialize_rename 'src/package_name/package_name.py', package_name + '.py' %}
{% template_specialize_rename 'src/package_name', package_name %}

{# Delete the package-name.txt utility template file #}
{% template_specialize_rename 'package-name.txt' %}
```

First, the "template_specialize_rename" extension is used to rename the package output files and directories. Finally,
since we don't want the empty utility file in the output, we delete it using the "template_specialize_rename" extension
with no second argument. Here's an example usage of our Python project template:

```
$ template-specialize python-package my-package -k package_name my_package
```

This command produces the following specialized template output with appropriately named package source directory and
source files:

```
.
|-- README.md
|-- setup.py
`-- src
    |-- __init__.py
    |-- my_package
    |   |-- __init__.py
    |   `-- my_package.py
    `-- tests
        |-- __init__.py
        `-- test_my_package.py
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
usage: template-specialize [-h] [-c FILE] [-e ENV] [-k KEY VALUE] [--dump]
                           SRC DST

positional arguments:
  SRC                   the source template file or directory
  DST                   the destination file or directory

options:
  -h, --help            show this help message and exit
  -c FILE               the environment files
  -e ENV                the environment name
  -k KEY VALUE, --key KEY VALUE
                        add a template key and value
  --dump                dump the template variables
```


## Development

This project is developed using [Python Build](https://github.com/craigahobbs/python-build#readme). It was started
using [python-package-template](https://github.com/craigahobbs/python-package-template#readme) as follows:

```
template-specialize python-package-template/template/ template-specialize/ -k package template-specialize -k name 'Craig A. Hobbs' -k email 'craigahobbs@gmail.com' -k github 'craigahobbs' -k nodoc 1
```
