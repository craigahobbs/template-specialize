# Copyright (C) 2017-2018 Craig Hobbs
#
# Licensed under the MIT License
# https://github.com/craigahobbs/template-specialize/blob/master/LICENSE

import re


class Environment:
    __slots__ = ('name', 'parents', 'values')

    def __init__(self, name, parents):
        self.name = name
        self.parents = parents
        self.values = {}

    @staticmethod
    def _parse_key_part(key_part):
        try:
            return int(key_part)
        except ValueError:
            return key_part

    @classmethod
    def _parse_key(cls, key_str):
        return tuple(cls._parse_key_part(part) for part in key_str.split('.'))

    @staticmethod
    def _parse_value(value_str):
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

    def add_value(self, key_str, value_str):
        key = self._parse_key(key_str)
        value = self._parse_value(value_str)
        if key in self.values:
            return None
        self.values[key] = value
        return key, value


class Environments(dict):
    __slots__ = ()

    _RE_COMMENT = re.compile(r'^\s*(?:#.*)?$')
    _RE_ENV = re.compile(r'^(?P<env>[A-Za-z_]\w*)(?:\s*\(\s*(?P<parents>[A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*)\s*\))?\s*:\s*$')
    _RE_VALUE = re.compile(r'^\s+(?P<key>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*|\.\d+)*)\s*=\s*(?P<value>"[^"]*"|\d+(?:\.\d*)?|true|false)\s*$')

    def add_environment(self, name, parents):
        if name in self:
            return None
        environment = self[name] = Environment(name, parents)
        return environment

    def parse(self, lines, filename=''):
        env_cur = None
        for ix_line, line in enumerate(lines.splitlines() if isinstance(lines, str) else lines):

            # Match the line
            match_comment = self._RE_COMMENT.search(line)
            if match_comment is None:
                match_env = self._RE_ENV.search(line)
                if match_env is None:
                    match_value = self._RE_VALUE.search(line)

            # Process the line
            if match_comment:
                pass
            elif match_env:
                env_name = match_env.group('env')
                env_parents_str = match_env.group('parents')
                env_parents = tuple(name.strip() for name in env_parents_str.split(',')) if env_parents_str is not None else ()
                env_cur = self.add_environment(env_name, env_parents)
                if env_cur is None:
                    raise SyntaxError('{0}:{1}: Redefinition of environment "{2}"'.format(filename, ix_line + 1, env_name))
            elif env_cur and match_value:
                key_str = match_value.group('key')
                value_str = match_value.group('value')
                if env_cur.add_value(key_str, value_str) is None:
                    raise SyntaxError('{0}:{1}: Redefinition of value "{2}"'.format(filename, ix_line + 1, key_str))
            else:
                raise SyntaxError('{0}:{1}: Syntax error : "{2}"'.format(filename, ix_line + 1, line))

    def asdict(self, environment_name, environment_dict=None):
        if environment_dict is None:
            environment_dict = {}

        for parent_name in self[environment_name].parents:
            self.asdict(parent_name, environment_dict)

        for key, value in sorted(self[environment_name].values.items()):
            container = environment_dict
            for idx in range(len(key) - 1):
                if isinstance(container, list):
                    if key[idx] < len(container):
                        container_next = container[key[idx]]
                    else:
                        if isinstance(key[idx + 1], int):
                            container_next = []
                        else:
                            container_next = {}
                        container.append(container_next)
                else:
                    container_next = container.get(key[idx])
                    if container_next is None:
                        if isinstance(key[idx + 1], int):
                            container_next = []
                        else:
                            container_next = {}
                        container[key[idx]] = container_next
                container = container_next
            if isinstance(container, list):
                if key[-1] < len(container):
                    container[key[-1]] = value
                else:
                    container.append(value)
            else:
                container[key[-1]] = value

        return environment_dict
