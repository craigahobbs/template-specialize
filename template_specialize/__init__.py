# Copyright (C) 2017-2018 Craig Hobbs
#
# Licensed under the MIT License
# https://github.com/craigahobbs/template-specialize/blob/master/LICENSE

import argparse
from itertools import chain
import os
import re
import sys

from jinja2 import Template, StrictUndefined


STATUS_UNKNOWN_ENVIRONMENT = 10


def main():

    # Command line parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('src_path', metavar='SRC',
                        help='the source template file or directory')
    parser.add_argument('dst_path', metavar='DST',
                        help='the destination file or directory')
    parser.add_argument('-c', dest='environment_files', metavar='FILE', action='append',
                        help='the environment files')
    parser.add_argument('-e', dest='environment', metavar='ENV',
                        help='the environment name - return status {0} if unknown environment'.format(STATUS_UNKNOWN_ENVIRONMENT))
    parser.add_argument('--key', action='append', dest='keys', metavar='KEY', default=[],
                        help='add a template key. Must be paired with a template value.')
    parser.add_argument('--value', action='append', dest='values', metavar='VALUE', default=[],
                        help='add a template value. Must be paired with a template key.')
    args = parser.parse_args()
    if len(args.keys) != len(args.values):
        parser.error('mismatched keys/values')

    # Parse the environment files
    environments = {}
    if args.environment_files:
        for environment_file in args.environment_files:
            with open(environment_file, 'r', encoding='utf-8') as f_environment:
                Environment.parse(f_environment, filename=environment_file, environments=environments)

    # Build the template variables dict
    if args.environment:
        if args.environment not in environments:
            parser.exit(status=STATUS_UNKNOWN_ENVIRONMENT, message='unknown environment "{0}"\n'.format(args.environment))
            extra_variables = [(Environment.parse_key(key), Environment.parse_value(value)) for key, value in zip(args.keys, args.values)]
        template_variables = Environment.asdict(environments, args.environment, extra_values=extra_variables)
    else:
        template_variables = dict(zip(args.keys, args.values))

    # Create the source and destination template file paths
    if os.path.isfile(args.src_path):
        src_files = [args.src_path]
        if args.dst_path.endswith(os.sep):
            dst_files = [os.path.join(args.dst_path, os.path.basename(args.src_path))]
        else:
            dst_files = [args.dst_path]
    else:
        src_files = list(chain.from_iterable((os.path.join(root, file_) for file_ in files) for root, _, files in os.walk(args.src_path)))
        dst_files = [os.path.join(args.dst_path, os.path.relpath(file_, args.src_path)) for file_ in src_files]

    # Process the template files
    for src_file, dst_file in zip(src_files, dst_files):
        os.makedirs(os.path.dirname(dst_file), exist_ok=True)
        with open(src_file, 'r', encoding='utf-8') as f_from:
            Template(f_from.read(), undefined=StrictUndefined).stream(**template_variables).dump(dst_file, encoding='utf-8')


class Environment:
    __slots__ = ('name', 'parents', 'values')

    def __init__(self, name, parents, values=None):
        self.name = name
        self.parents = parents
        self.values = [] if values is None else values

    _RE_COMMENT = re.compile(r'^\s*(?:#.*)?$')
    _RE_ENV = re.compile(r'^(?P<env>\w+)(?:\s*\(\s*(?P<parents>\w+(?:\s*,\s*\w*)*)\s*\))?\s*:\s*$')
    _RE_VALUE = re.compile(r'^\s+(?P<key>[A-Za-z_-]+(?:\.\w+)*)\s*=\s*(?P<value>"[^"]*"|[0-9]+(?:\.[0-9]*)?|true|false)\s*$')

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
