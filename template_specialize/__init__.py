# Copyright (C) 2017 Craig Hobbs
#
# Licensed under the MIT License
# https://github.com/craigahobbs/template-specialize/blob/master/LICENSE

import argparse
from itertools import chain
import os
import re
import sys

from jinja2 import Template, StrictUndefined


STATUS_ENVIRONMENT_NOT_FOUND = 10


def main():

    # Command line parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('from_path', metavar='FROM',
                        help='The template "from" file or directory')
    parser.add_argument('to_dir', metavar='TO',
                        help='The template "to" directory')
    parser.add_argument('-c', dest='config_value_files', metavar='FILE', action='append',
                        help='one or more config value files')
    parser.add_argument('-e', dest='environment', metavar='ENV',
                        help='environment name - return status {0} if environment is not found'.format(STATUS_ENVIRONMENT_NOT_FOUND))
    parser.add_argument('--key', action='append', dest='keys', metavar='KEY', default=[],
                        help='add a template key. Must be paired with a template value.')
    parser.add_argument('--value', action='append', dest='values', metavar='VALUE', default=[],
                        help='add a template value. Must be paired with a template key.')
    args = parser.parse_args()

    if len(args.keys) != len(args.values):
        parser.error('mismatched keys/values')

    # Parse the config files
    environments = {}
    for config_value_file in args.config_value_files:
        with open(config_value_file, 'r') as config:
            Environment.parse(config, filename=config_value_file, environments=environments)

    # Build the environment config values dict
    if args.environment not in environments:
        parser.exit(status=STATUS_ENVIRONMENT_NOT_FOUND, message='environment "{0}" not found\n'.format(args.environment))
    extra_values = [
        (Environment.parse_key(key), Environment.parse_value(value)) for key, value in chain.from_iterable([
            [
                ('environment.fqdn', 'localhost'),
                ('environment.hostname', 'localhost'),
                ('environment.name', args.environment),
            ],
            zip(args.keys, args.values)
        ])
    ]
    config_values = Environment.asdict(environments, args.environment, extra_values=extra_values)

    # Create the relative template file paths
    if os.path.isfile(args.from_path):
        from_dir_root = os.path.dirname(args.from_path) or '.'
        from_files = [os.path.basename(args.from_path)]
    else:
        from_dir_root = args.from_path
        assert os.path.isdir(from_dir_root), '"{0}" is not a directory'.format(from_dir_root)
        from_files = list(chain.from_iterable(
            (os.path.relpath(os.path.join(root, file_), from_dir_root) for file_ in files)
            for root, dirs, files in os.walk(args.from_path)
        ))

    # Process the template files
    to_dir_root = args.to_dir
    for file_rel in from_files:
        from_file = os.path.join(from_dir_root, file_rel)
        to_file = os.path.join(to_dir_root, file_rel)

        # Ensure the "to" directory exists
        to_dir = os.path.dirname(to_file)
        if os.path.exists(to_dir):
            assert os.path.isdir(to_dir), '"{0}" is not a directory'.format(to_dir)
        else:
            os.makedirs(to_dir)

        # Process the template
        with open(from_file, 'r') as f_from:
            Template(f_from.read(), undefined=StrictUndefined).stream(**config_values).dump(to_file)


class Environment(object):
    __slots__ = ('name', 'parents', 'values')

    def __init__(self, name, parents, values=None):
        self.name = name
        self.parents = parents
        self.values = [] if values is None else values

    _RE_COMMENT = re.compile(r'^\s*(?:#.*)?$')
    _RE_ENV = re.compile(r'^(?P<env>\w+)(?:\s*\(\s*(?P<parents>\w+(?:\s*,\s*\w*)*)\s*\))?\s*:\s*$')
    _RE_PART_KEY = r'[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*'
    _RE_VALUE = re.compile(r'^\s+(?P<key>' + _RE_PART_KEY + r')\s*=\s*(?P<value>"[^"]*"|[0-9]+(?:\.[0-9]*)?|true|false)\s*$')

    @staticmethod
    def _parse_key_part(key_part):
        try:
            return int(key_part)
        except ValueError:
            return key_part

    @classmethod
    def parse_key(cls, key_str):
        return tuple(cls._parse_key_part(part) for part in key_str.split('.'))

    @staticmethod
    def parse_value(value_str):
        if value_str == 'true':
            return True
        elif value_str == 'false':
            return False
        elif value_str.startswith('"'):
            return value_str[1:-1]
        try:
            return int(value_str)
        except ValueError:
            pass
        try:
            return float(value_str)
        except ValueError:
            pass
        return value_str

    @classmethod
    def parse(cls, lines, filename='', environments=None):
        envs = environments if environments is not None else {}
        env_cur = None
        for ix_line, line in enumerate(lines.splitlines() if isinstance(lines, str) else lines):

            # Match the line
            match_comment = cls._RE_COMMENT.search(line)
            if match_comment is None:
                match_env = cls._RE_ENV.search(line)
                if match_env is None:
                    match_value = cls._RE_VALUE.search(line)

            # Process the line
            if match_comment:
                pass
            elif match_env:
                env_name = match_env.group('env')
                env_parents = match_env.group('parents')
                if env_parents is not None:
                    env_parents = [parent.strip() for parent in env_parents.split(',')]
                env_cur = envs[env_name] = envs.get(env_name)
                if not env_cur or (not env_cur.parents and env_parents):
                    env_cur = envs[env_name] = Environment(env_name, env_parents, values=env_cur and env_cur.values)
                elif env_parents and not env_parents == env_cur.parents:
                    raise SyntaxError('{0}:{1}: Inconsistent definition of environment "{2}"'.format(filename, ix_line + 1, env_name))
            elif env_cur and match_value:
                key_str = match_value.group('key')
                key = cls.parse_key(key_str)
                value = cls.parse_value(match_value.group('value'))
                key_value = (key, value, env_cur.name)
                if any(e == env_cur.name for k, _, e in env_cur.values if k == key):
                    raise SyntaxError('{0}:{1}: Redefinition of value "{2}"'.format(filename, ix_line + 1, key_str))
                env_cur.values.append(key_value)
            else:
                raise SyntaxError('{0}:{1}: Syntax error : "{2}"'.format(filename, ix_line + 1, line))

        return envs

    @classmethod
    def asdict(cls, environments, environment_name, extra_values=None, container=None):
        if container is None:
            container = {}
        if extra_values is not None:
            new_lists = []
            for key, value in extra_values:
                cls._add_value(container, key, value, new_lists)
        new_lists = []
        for key, value, _ in sorted(environments[environment_name].values):
            cls._add_value(container, key, value, new_lists)
        if environments[environment_name].parents is not None:
            for parent_name in environments[environment_name].parents:
                cls.asdict(environments, parent_name, container=container)
        return container

    @staticmethod
    def _add_value(container, key, value, new_lists):
        for idx in range(len(key) - 1):
            subkey = key[idx]
            if subkey in container:
                container_next = container[subkey]
            elif isinstance(key[idx + 1], int):
                container_next = []
                new_lists.append(container_next)
            else:
                container_next = {}
            container[subkey] = container_next
            container = container_next
        if isinstance(container, list):
            if container in new_lists:
                container.append(value)
        else:
            if key[-1] not in container:
                container[key[-1]] = value
