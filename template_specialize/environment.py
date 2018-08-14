# Copyright (C) 2017-2018 Craig Hobbs
#
# Licensed under the MIT License
# https://github.com/craigahobbs/template-specialize/blob/master/LICENSE

from collections import namedtuple
import re


class EnvironmentKeyValue(namedtuple('EnvironmentKeyValue', ('key', 'value', 'filename', 'lineno'))):

    def __new__(cls, key_str, value_str, filename='', lineno=0):
        return super().__new__(cls, cls._parse_key(key_str), cls._parse_value(value_str), filename, lineno)

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

    def __lt__(self, other):
        try:
            return super().__lt__(other)
        except TypeError:
            key = self.key
            part = next(part for part, other_part in zip(key, other.key) if not isinstance(part, type(other_part))) # pragma: no branch
            return isinstance(part, int)


class Environment(namedtuple('Environment', ('name', 'parents', 'values', 'filename', 'lineno'))):
    __slots__ = ()

    def __new__(cls, name, parents, filename='', lineno=0):
        return super().__new__(cls, name, parents, [], filename, lineno)

    def add_value(self, key_str, value_str, filename='', lineno=0, errors=None):
        key_value = EnvironmentKeyValue(key_str, value_str, filename, lineno)
        key = key_value.key
        if any(kv.key == key for kv in self.values):
            if errors is not None:
                errors.append('{0}:{1}: Redefinition of value "{2}"'.format(filename, lineno, key_str))
            return None
        self.values.append(key_value)
        return key_value


class Environments(dict):
    __slots__ = ()

    _RE_COMMENT = re.compile(r'^\s*(?:#.*)?$')
    _RE_ENV = re.compile(r'^(?P<env>[A-Za-z_]\w*)(?:\s*\(\s*(?P<parents>[A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*)\s*\))?\s*:\s*$')
    _RE_VALUE = re.compile(r'^\s+(?P<key>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*|\.\d+)*)\s*=\s*(?P<value>"[^"]*"|\d+(?:\.\d*)?|true|false)\s*$')

    def add_environment(self, name, parents, filename='', lineno=0, errors=None):
        environment = self.get(name)
        if environment is not None:
            if parents != environment.parents and errors is not None:
                errors.append('{0}:{1}: Redefinition of environment "{2}"'.format(filename, lineno, name))
        else:
            environment = self[name] = Environment(name, parents, filename=filename, lineno=lineno)
        return environment

    def parse(self, lines, filename='', errors=None):
        if errors is None:
            errors = []
        env_cur = None
        for ix_line, line in enumerate(line.rstrip() for line in (lines.splitlines() if isinstance(lines, str) else lines)): # pylint: disable=superfluous-parens

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
                env_cur = self.add_environment(env_name, env_parents, filename=filename, lineno=ix_line + 1, errors=errors)
            elif env_cur and match_value:
                key_str = match_value.group('key')
                value_str = match_value.group('value')
                env_cur.add_value(key_str, value_str, filename=filename, lineno=ix_line + 1, errors=errors)
            else:
                errors.append('{0}:{1}: Syntax error: "{2}"'.format(filename, ix_line + 1, line))

        return errors

    def check(self, errors=None):
        if errors is None:
            errors = []
        for env_name in sorted(self.keys()):
            for _ in self._iterate_values(env_name, errors=errors):
                pass
        return errors

    def asdict(self, environment_name):
        environment_dict = {}
        for key_value in self._iterate_values(environment_name):
            key = key_value.key
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
                        container.append(container_next) # pylint: disable=no-member
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
                    container[key[-1]] = key_value.value
                else:
                    container.append(key_value.value)
            else:
                container[key[-1]] = key_value.value

        return environment_dict

    def _iterate_values(self, environment_name, errors=None):
        lists = {}
        types = {}
        circulars = set()
        for key_value in self._iterate_values_inner(environment_name, circulars, errors=errors):
            key = key_value.key
            skip = False

            for idx in range(len(key) - 1):
                subkey = key[:idx + 1]

                # Check array indexes
                list_index = key[idx + 1]
                if isinstance(list_index, int):
                    list_length = lists.get(subkey, 0)
                    if list_index > list_length:
                        skip = True
                        if errors is not None:
                            error = '{0}:{1}: Invalid list index "{2}"'.format(
                                key_value.filename, key_value.lineno, '.'.join(str(x) for x in key[:idx + 2])
                            )
                            if error not in errors:
                                errors.append(error)
                    else:
                        lists[subkey] = max(list_length, list_index + 1)

                # Check for container type change
                type_ = types.get(subkey)
                if type_ is None:
                    types[subkey] = type(key[idx + 1])
                else:
                    if not isinstance(key[idx + 1], type_):
                        skip = True
                        if errors is not None:
                            error = '{0}:{1}: Redefinition of container type "{2}"'.format(
                                key_value.filename, key_value.lineno, '.'.join(str(x) for x in subkey)
                            )
                            if error not in errors:
                                errors.append(error)

            # Check for value type change
            type_ = types.get(key)
            if key not in types:
                types[key] = type(None)
            else:
                if type_ is not type(None):
                    skip = True
                    if errors is not None:
                        error = '{0}:{1}: Redefinition of container type "{2}"'.format(
                            key_value.filename, key_value.lineno, '.'.join(str(x) for x in key)
                        )
                        if error not in errors:
                            errors.append(error)

            if not skip:
                yield key_value

    def _iterate_values_inner(self, environment_name, circulars, errors=None):
        environment = self[environment_name]
        for parent_name in environment.parents:
            skip = False

            # Check for unknown environment inheritance
            if parent_name not in self:
                if errors is not None:
                    error = '{0}:{1}: Environment "{2}" has unknown parent environment "{3}"'.format(
                        environment.filename, environment.lineno, environment.name, parent_name
                    )
                    if error not in errors:
                        errors.append(error)
                skip = True

            # Check for circular environment inheritance
            if parent_name in circulars:
                if errors is not None:
                    error = '{0}:{1}: Environment "{2}" has circular parent environment "{3}"'.format(
                        environment.filename, environment.lineno, environment.name, parent_name
                    )
                    if error not in errors:
                        errors.append(error)
                skip = True

            if not skip:
                circulars.add(parent_name)
                yield from self._iterate_values_inner(parent_name, circulars, errors=errors)
                circulars.remove(parent_name)

        yield from sorted(environment.values)
