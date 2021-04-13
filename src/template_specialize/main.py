# Licensed under the MIT License
# https://github.com/craigahobbs/template-specialize/blob/main/LICENSE

import argparse
from itertools import chain
import os
import sys
import warnings

from jinja2 import Environment, StrictUndefined
import yaml

from . import __version__ as VERSION
from .aws_parameter_store import ParameterStoreExtension


def main(argv=None):

    # Command line parsing
    parser = argparse.ArgumentParser(prog='template-specialize')
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
    parser.add_argument('--dump', action='store_true',
                        help='dump the template variables')
    parser.add_argument('-v', '--version', action='store_true',
                        help='show version number and quit')
    args = parser.parse_args(args=argv)
    if args.version:
        parser.exit(message=VERSION + '\n')
    if len(args.keys) != len(args.values):
        parser.error('mismatched keys/values')

    # Parse the environment files
    environments = {}
    if args.environment_files:
        for environment_file in args.environment_files:
            try:
                with open(environment_file, 'r', encoding='utf-8') as f_environment:
                    _parse_environments(f_environment, environments)
            except Exception as exc: # pylint: disable=broad-except
                parser.exit(message=str(exc) + '\n', status=2)

    # Build the template variables dict
    template_variables = {}
    try:
        if args.environment is not None:
            _merge_environment(environments, args.environment, template_variables, set())
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', DeprecationWarning)
            for key, value in zip(args.keys, args.values):
                _merge_values({key: yaml.full_load(value)}, template_variables)
    except Exception as exc: # pylint: disable=broad-except
        parser.exit(message=str(exc) + '\n', status=2)

    # Dump the template variables, if necessary
    if args.dump:
        parser.exit(message=yaml.dump(template_variables, default_flow_style=False))

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
    environment = Environment(extensions=[ParameterStoreExtension], undefined=StrictUndefined)
    try:
        for src_file, dst_file in zip(src_files, dst_files):
            if is_dir:
                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            if isinstance(src_file, str):
                f_src = open(src_file, 'r', encoding='utf-8')
            else:
                f_src = src_file
            try:
                dst_encoding = None
                if isinstance(dst_file, str):
                    dst_encoding = 'utf-8'
                environment.from_string(f_src.read()).stream(**template_variables).dump(dst_file, encoding=dst_encoding)
            finally:
                if f_src is not src_file:
                    f_src.close()
    except Exception as exc: # pylint: disable=broad-except
        parser.exit(message=str(exc) + '\n', status=2)


def _parse_environments(environment_yaml, environments):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', DeprecationWarning)
        loaded_environments = yaml.full_load(environment_yaml)
    if not isinstance(loaded_environments, dict):
        raise ValueError('invalid environments container: {0!r:.100s}'.format(loaded_environments))
    for environment_name, environment_info in loaded_environments.items():
        if not isinstance(environment_name, str):
            raise ValueError('invalid environment name {0!r:.100s}'.format(environment_name))
        if environment_name in environments:
            raise ValueError('redefinition of environment {0!r:.100s}'.format(environment_name))
        if not isinstance(environment_info, dict):
            raise ValueError('invalid environment metadata for environment {0!r:.100s}: {1!r:.100s}'.format(
                environment_name, environment_info
            ))
        environment_parents = environment_info.get('parents')
        if (environment_parents is not None and not isinstance(environment_parents, list)) or \
           (environment_parents is not None and not all(isinstance(name, str) for name in environment_parents)):
            raise ValueError('invalid parents for environment {0!r:.100s}: {1!r:.100s}'.format(
                environment_name, environment_parents
            ))
        environment_values = environment_info.get('values')
        if environment_values is not None and not isinstance(environment_values, dict):
            raise ValueError('invalid values for environment {0!r:.100s}: {1!r:.100s}'.format(
                environment_name, environment_values
            ))
        environments[environment_name] = environment_info


def _merge_environment(environments, name, values, visited):
    environment = environments.get(name)
    if environment is None:
        raise ValueError('unknown environment {0!r:.100}'.format(name))
    environment_parents = environment.get('parents')
    if environment_parents is not None:
        for environment_parent in environment_parents:
            if environment_parent in visited:
                raise ValueError('circular inheritance with environment {0!r:.100s}'.format(environment_parent))
            visited.add(environment_parent)
            values = _merge_environment(environments, environment_parent, values, visited)
            visited.remove(environment_parent)
    environment_values = environment.get('values')
    if environment_values is not None:
        values = _merge_values(environment_values, values)
    return values


def _merge_values(src, dst):
    if isinstance(src, list):
        if not isinstance(dst, list):
            dst = []
        len_dst = len(dst)
        for idx, src_value in enumerate(src):
            if idx < len_dst:
                dst[idx] = _merge_values(src_value, dst[idx])
            else:
                dst.append(_merge_values(src_value, None))
        return dst
    if isinstance(src, dict):
        if not isinstance(dst, dict):
            dst = {}
        for key, src_value in src.items():
            dst[key] = _merge_values(src_value, dst.get(key))
        return dst
    return src
