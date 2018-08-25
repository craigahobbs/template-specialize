# Copyright (C) 2017-2018 Craig Hobbs
#
# Licensed under the MIT License
# https://github.com/craigahobbs/template-specialize/blob/master/LICENSE

import argparse
from itertools import chain
import os
import sys

try:
    from jinja2 import Template, StrictUndefined
except ImportError: # pragma: no cover
    pass

from . import __version__ as VERSION
from .environment import Environments


def main(argv=None):

    # Command line parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('src_path', metavar='SRC', nargs='?',
                        help='the source template file or directory')
    parser.add_argument('dst_path', metavar='DST', nargs='?',
                        help='the destination file or directory')
    parser.add_argument('-c', dest='environment_files', metavar='FILE', action='append',
                        help='the environment files')
    parser.add_argument('-e', dest='environment', metavar='ENV',
                        help='the environment name')
    parser.add_argument('--key', action='append', dest='keys', metavar='KEY', default=[],
                        help='add a template key. Must be paired with a template value.')
    parser.add_argument('--value', action='append', dest='values', metavar='VALUE', default=[],
                        help='add a template value. Must be paired with a template key.')
    parser.add_argument('-v', '--version', action='store_true',
                        help='show version number and quit')
    args = parser.parse_args(args=argv)
    if args.version:
        parser.exit(message=VERSION + '\n')
    if len(args.keys) != len(args.values):
        parser.error('mismatched keys/values')

    # Parse the environment files
    environments = Environments()
    errors = []
    if args.environment_files:
        for environment_file in args.environment_files:
            with open(environment_file, 'r', encoding='utf-8') as f_environment:
                environments.parse(f_environment, filename=environment_file, errors=errors)

    # Build the template variables dict
    if args.environment is None:
        environment = environments.add_environment('', [])
    else:
        if args.environment not in environments:
            parser.error('unknown environment "{0}"'.format(args.environment))
        environment = environments.add_environment('', [args.environment])
    for idx, (key, value) in enumerate(zip(args.keys, args.values)):
        environment.add_value(key, value, lineno=idx + 1, errors=errors)
    environments.check(errors=errors)
    if errors:
        parser.exit(message='\n'.join(errors) + '\n', status=2)
    template_variables = environments.asdict('')

    # Create the source template file paths
    is_dir = False
    if not args.src_path or args.src_path == '-':
        src_files = [sys.stdin]
    elif os.path.isdir(args.src_path):
        is_dir = True
        src_files = list(chain.from_iterable((os.path.join(root, file_) for file_ in files) for root, _, files in os.walk(args.src_path)))
    else:
        src_files = [args.src_path]

    # Create the destination template file paths
    if is_dir:
        dst_files = [os.path.join(args.dst_path, os.path.relpath(file_, args.src_path)) for file_ in src_files]
    elif not args.dst_path or args.dst_path == '-':
        dst_files = [sys.stdout]
    else:
        dst_files = [args.dst_path]

    # Process the template files
    try:
        for src_file, dst_file in zip(src_files, dst_files):
            if is_dir:
                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            if isinstance(src_file, str):
                f_src = open(src_file, 'r', encoding='utf-8')
            else:
                f_src = src_file
            try:
                if isinstance(dst_file, str):
                    dst_encoding = 'utf-8'
                else:
                    dst_encoding = None
                Template(f_src.read(), undefined=StrictUndefined).stream(**template_variables).dump(dst_file, encoding=dst_encoding)
            finally:
                if f_src is not src_file:
                    f_src.close()
    except Exception as exc: # pylint: disable=broad-except
        parser.exit(message=str(exc) + '\n', status=2)
