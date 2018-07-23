# Copyright (C) 2017-2018 Craig Hobbs
#
# Licensed under the MIT License
# https://github.com/craigahobbs/template-specialize/blob/master/LICENSE

import re


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
        return float(value_str)

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
            for parent_name in reversed(environments[environment_name].parents):
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
