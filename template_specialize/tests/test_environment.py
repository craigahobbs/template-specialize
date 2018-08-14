# Copyright (C) 2017-2018 Craig Hobbs
#
# Licensed under the MIT License
# https://github.com/craigahobbs/template-specialize/blob/master/LICENSE

from template_specialize.environment import EnvironmentKeyValue, Environment, Environments

from . import TestCase


class TestEnvironmentKeyValue(TestCase):

    def test_new(self):
        self.assertTupleEqual(
            EnvironmentKeyValue('a.b.0.c.1', 'true'),
            (('a', 'b', 0, 'c', 1), True, '', 0)
        )
        self.assertTupleEqual(
            EnvironmentKeyValue('a', 'false'),
            (('a',), False, '', 0)
        )
        self.assertTupleEqual(
            EnvironmentKeyValue('a', '7'),
            (('a',), 7, '', 0)
        )
        self.assertTupleEqual(
            EnvironmentKeyValue('a', '3.14'),
            (('a',), 3.14, '', 0)
        )
        self.assertTupleEqual(
            EnvironmentKeyValue('a', '"abc"'),
            (('a',), 'abc', '', 0)
        )
        self.assertTupleEqual(
            EnvironmentKeyValue('a', 'abc'),
            (('a',), 'abc', '', 0)
        )
        self.assertTupleEqual(
            EnvironmentKeyValue('a', '"abc"', 'test.config', 7),
            (('a',), 'abc', 'test.config', 7)
        )

    def test_lt(self):
        self.assertListEqual(
            sorted([
                EnvironmentKeyValue('a.0', '0'),
                EnvironmentKeyValue('b.0', '1'),
                EnvironmentKeyValue('a.1', '2'),
                EnvironmentKeyValue('b.1', '3'),
                EnvironmentKeyValue('b.1', '3.5'),
                EnvironmentKeyValue('b.1.b', '4'),
                EnvironmentKeyValue('b.1.2', '5'),
                EnvironmentKeyValue('b.1.5', '6'),
                EnvironmentKeyValue('b.a.2', '7')
            ]),
            [
                (('a', 0), 0, '', 0),
                (('a', 1), 2, '', 0),
                (('b', 0), 1, '', 0),
                (('b', 1), 3, '', 0),
                (('b', 1), 3.5, '', 0),
                (('b', 1, 2), 5, '', 0),
                (('b', 1, 5), 6, '', 0),
                (('b', 1, 'b'), 4, '', 0),
                (('b', 'a', 2), 7, '', 0)
            ]
        )


class TestEnvironment(TestCase):

    def test_new(self):
        self.assertEqual(
            Environment('env', ('env2', 'env3')),
            ('env', ('env2', 'env3'), [], '', 0)
        )
        self.assertEqual(
            Environment('env', ('env2', 'env3'), 'test.config', 7),
            ('env', ('env2', 'env3'), [], 'test.config', 7)
        )

    def test_add_value(self):
        environment = Environment('env', ())

        self.assertEqual(
            environment.add_value('a.0.b', 'true'),
            (('a', 0, 'b'), True, '', 0)
        )
        self.assertEqual(
            environment.add_value('a.1.b', 'false'),
            (('a', 1, 'b'), False, '', 0)
        )
        self.assertEqual(
            environment.add_value('a.2.b', '"string"'),
            (('a', 2, 'b'), 'string', '', 0)
        )
        self.assertEqual(
            environment.add_value('a.3.b', '7'),
            (('a', 3, 'b'), 7, '', 0)
        )
        self.assertEqual(
            environment.add_value('a.4.b', '3.14'),
            (('a', 4, 'b'), 3.14, '', 0)
        )
        self.assertEqual(
            environment.add_value('a.5.b', 'asdf'),
            (('a', 5, 'b'), 'asdf', '', 0)
        )
        self.assertIsNone(
            environment.add_value('a.5.b', '11')
        )

        self.assertEqual(environment.name, 'env')
        self.assertTupleEqual(environment.parents, ())
        self.assertListEqual(environment.values, [
            (('a', 0, 'b'), True, '', 0),
            (('a', 1, 'b'), False, '', 0),
            (('a', 2, 'b'), 'string', '', 0),
            (('a', 3, 'b'), 7, '', 0),
            (('a', 4, 'b'), 3.14, '', 0),
            (('a', 5, 'b'), 'asdf', '', 0)
        ])


class TestEnvironments(TestCase):

    def test_add_environment(self):
        environments = Environments()
        environment = environments.add_environment('env', [])
        environment2 = environments.add_environment('env2', ['env'])
        environments.add_environment('env2', [])
        self.assertListEqual(sorted(environments.keys()), ['env', 'env2'])
        self.assertIs(environment, environments['env'])
        self.assertEqual(environment.name, 'env')
        self.assertEqual(environment.parents, [])
        self.assertEqual(environment.values, [])
        self.assertIs(environment2, environments['env2'])
        self.assertEqual(environment2.name, 'env2')
        self.assertEqual(environment2.parents, ['env'])
        self.assertEqual(environment2.values, [])

    def test_parse(self):
        environments = Environments()
        errors = environments.parse('''\
# The first environment
env1:
    a.a = "foo"
    a.b = 12
    a.c = 12.5
    a.d = true
    b.0 = "bonk"

# The second environment
env2:
    a.a = "bar"
    a.b = 19
    a.c = 19.5
    a.d = false
    b.0 = "thud"
''')
        self.assertListEqual(errors, [])
        self.assertListEqual(environments.check(), [])
        self.assertListEqual(sorted(environments.keys()), ['env1', 'env2'])
        self.assertTupleEqual(environments['env1'].parents, ())
        self.assertListEqual(environments['env1'].values, [
            (('a', 'a'), 'foo', '', 3),
            (('a', 'b'), 12, '', 4),
            (('a', 'c'), 12.5, '', 5),
            (('a', 'd'), True, '', 6),
            (('b', 0), 'bonk', '', 7)
        ])
        self.assertTupleEqual(environments['env2'].parents, ())
        self.assertListEqual(environments['env2'].values, [
            (('a', 'a'), 'bar', '', 11),
            (('a', 'b'), 19, '', 12),
            (('a', 'c'), 19.5, '', 13),
            (('a', 'd'), False, '', 14),
            (('b', 0), 'thud', '', 15)
        ])

    def test_parse_parent(self):
        environments = Environments()
        errors = environments.parse('''\
base:
    a.a = "foo"
    a.b = 12

base2:
    b.a = "thud"

env(base, base2):
    a.b = 19
    a.c = "bar"
    a.d = "env a.d"
    a.e = "env a.e"
''')
        self.assertListEqual(errors, [])
        self.assertListEqual(environments.check(), [])
        self.assertListEqual(sorted(environments.keys()), ['base', 'base2', 'env'])
        self.assertTupleEqual(environments['base'].parents, ())
        self.assertListEqual(environments['base'].values, [
            (('a', 'a'), 'foo', '', 2),
            (('a', 'b'), 12, '', 3)
        ])
        self.assertTupleEqual(environments['base2'].parents, ())
        self.assertListEqual(environments['base2'].values, [
            (('b', 'a'), 'thud', '', 6)
        ])
        self.assertTupleEqual(environments['env'].parents, ('base', 'base2'))
        self.assertListEqual(environments['env'].values, [
            (('a', 'b'), 19, '', 9),
            (('a', 'c'), 'bar', '', 10),
            (('a', 'd'), 'env a.d', '', 11),
            (('a', 'e'), 'env a.e', '', 12)
        ])

    def test_parse_errors(self):
        environments = Environments()
        errors = ['hello']
        errors_parse = environments.parse('asdf', errors=errors)
        self.assertIs(errors, errors_parse)
        self.assertListEqual(errors, [
            'hello',
            ':1: Syntax error: "asdf"'
        ])

    def test_parse_syntax_error(self):
        environments = Environments()
        errors = environments.parse('''\
env:
    a.a = "foo"
    a.b = foo
    a.c = 12
''')
        self.assertListEqual(errors, [
            ':3: Syntax error: "    a.b = foo"'
        ])
        self.assertListEqual(environments.check(), [])
        self.assertListEqual(sorted(environments.keys()), ['env'])
        self.assertTupleEqual(environments['env'].parents, ())
        self.assertListEqual(environments['env'].values, [
            (('a', 'a'), 'foo', '', 2),
            (('a', 'c'), 12, '', 4)
        ])

    def test_parse_environment_redefinition(self): # pylint: disable=invalid-name
        environments = Environments()
        errors = environments.parse('''\
env:
    a = "foo"

env(env2):
    b = "bar"

env:
    c = "bonk"
''')
        self.assertListEqual(errors, [
            ':4: Redefinition of environment "env"'
        ])
        self.assertListEqual(environments.check(), [])
        self.assertListEqual(sorted(environments.keys()), ['env'])
        self.assertTupleEqual(environments['env'].parents, ())
        self.assertListEqual(environments['env'].values, [
            (('a',), 'foo', '', 2),
            (('b',), 'bar', '', 5),
            (('c',), 'bonk', '', 8)
        ])

    def test_parse_value_redefinition(self):
        environments = Environments()
        errors = environments.parse('''\
env:
    a = "foo"
    a = "bar"
''')
        self.assertListEqual(errors, [
            ':3: Redefinition of value "a"'
        ])
        self.assertListEqual(environments.check(), [])
        self.assertListEqual(sorted(environments.keys()), ['env'])
        self.assertTupleEqual(environments['env'].parents, ())
        self.assertListEqual(environments['env'].values, [
            (('a',), 'foo', '', 2)
        ])

    def test_parse_type_change(self):
        environments = Environments()
        errors = environments.parse('''\
env:
    a.b.0 = "env a.b.0"
    a.b.1 = "env a.b.1"
    b.0 = "env b.0"
    c.a = "env c.a"
    d.0.0 = "env d.0.0"
    e.a.a = "env e.a.a"

env2(env):
    a.b.a = "env2 a.b.a"
    b.0.a = "env2 b.0.a"
    c.0 = "env2 c.0"
    d.0.a = "env2 d.0.a"
    e.a = "env2 e.a"

env3(env2):
''')
        self.assertListEqual(errors, [])
        self.assertListEqual(environments.check(), [
            ':10: Redefinition of container type "a.b"',
            ':11: Redefinition of container type "b.0"',
            ':12: Redefinition of container type "c"',
            ':13: Redefinition of container type "d.0"',
            ':14: Redefinition of container type "e.a"'
        ])
        self.assertListEqual(sorted(environments.keys()), ['env', 'env2', 'env3'])
        self.assertEqual(environments['env'].name, 'env')
        self.assertTupleEqual(environments['env'].parents, ())
        self.assertListEqual(environments['env'].values, [
            (('a', 'b', 0), 'env a.b.0', '', 2),
            (('a', 'b', 1), 'env a.b.1', '', 3),
            (('b', 0), 'env b.0', '', 4),
            (('c', 'a'), 'env c.a', '', 5),
            (('d', 0, 0), 'env d.0.0', '', 6),
            (('e', 'a', 'a'), 'env e.a.a', '', 7)
        ])
        self.assertEqual(environments['env2'].name, 'env2')
        self.assertTupleEqual(environments['env2'].parents, ('env',))
        self.assertListEqual(environments['env2'].values, [
            (('a', 'b', 'a'), 'env2 a.b.a', '', 10),
            (('b', 0, 'a'), 'env2 b.0.a', '', 11),
            (('c', 0), 'env2 c.0', '', 12),
            (('d', 0, 'a'), 'env2 d.0.a', '', 13),
            (('e', 'a'), 'env2 e.a', '', 14)
        ])
        self.assertEqual(environments['env3'].name, 'env3')
        self.assertTupleEqual(environments['env3'].parents, ('env2',))
        self.assertListEqual(environments['env3'].values, [])

    def test_check_no_errors(self):
        environments = Environments()
        errors = environments.parse('''\
env:
    a.b.c = 1

env2(env):
    a.b.c = 2
    a.b.d = 3

env3(env):
    a.b.e = 4

env4(env2, env3):
    a.b.f = 5
''')
        self.assertListEqual(errors, [])
        self.assertListEqual(environments.check(), [])
        self.assertListEqual(sorted(environments.keys()), ['env', 'env2', 'env3', 'env4'])
        self.assertEqual(environments['env'].name, 'env')
        self.assertTupleEqual(environments['env'].parents, ())
        self.assertListEqual(environments['env'].values, [
            (('a', 'b', 'c'), 1, '', 2)
        ])
        self.assertEqual(environments['env2'].name, 'env2')
        self.assertTupleEqual(environments['env2'].parents, ('env',))
        self.assertListEqual(environments['env2'].values, [
            (('a', 'b', 'c'), 2, '', 5),
            (('a', 'b', 'd'), 3, '', 6)
        ])
        self.assertEqual(environments['env3'].name, 'env3')
        self.assertTupleEqual(environments['env3'].parents, ('env',))
        self.assertListEqual(environments['env3'].values, [
            (('a', 'b', 'e'), 4, '', 9),
        ])
        self.assertEqual(environments['env4'].name, 'env4')
        self.assertTupleEqual(environments['env4'].parents, ('env2', 'env3'))
        self.assertListEqual(environments['env4'].values, [
            (('a', 'b', 'f'), 5, '', 12),
        ])

    def test_check_errors(self):
        environments = Environments()
        errors = ['hello']
        environments.add_environment('env', ['env2'], errors=errors)
        environments.add_environment('env2', ['env'], errors=errors)
        self.assertListEqual(errors, ['hello'])
        errors_check = environments.check(errors=errors)
        self.assertIs(errors_check, errors)
        self.assertListEqual(errors, [
            'hello',
            ':0: Environment "env" has circular parent environment "env2"',
            ':0: Environment "env2" has circular parent environment "env"'
        ])

    def test_check_unknown(self):
        environments = Environments()
        errors = environments.parse('''\
env:
    a.b.c = 1

env2(env, env5):
    a.b.c = 2
    a.b.d = 3

env3(env2):
    a.b.e = 4
''')
        self.assertListEqual(errors, [])
        self.assertListEqual(environments.check(), [
            ':4: Environment "env2" has unknown parent environment "env5"'
        ])
        self.assertListEqual(sorted(environments.keys()), ['env', 'env2', 'env3'])
        self.assertEqual(environments['env'].name, 'env')
        self.assertTupleEqual(environments['env'].parents, ())
        self.assertListEqual(environments['env'].values, [
            (('a', 'b', 'c'), 1, '', 2)
        ])
        self.assertEqual(environments['env2'].name, 'env2')
        self.assertTupleEqual(environments['env2'].parents, ('env', 'env5'))
        self.assertListEqual(environments['env2'].values, [
            (('a', 'b', 'c'), 2, '', 5),
            (('a', 'b', 'd'), 3, '', 6)
        ])
        self.assertEqual(environments['env3'].name, 'env3')
        self.assertTupleEqual(environments['env3'].parents, ('env2',))
        self.assertListEqual(environments['env3'].values, [
            (('a', 'b', 'e'), 4, '', 9),
        ])

    def test_check_circular(self):
        environments = Environments()
        errors = environments.parse('''\
env(env2):

env2(env):

env3(env):
''')
        self.assertListEqual(errors, [])
        self.assertListEqual(environments.check(), [
            ':1: Environment "env" has circular parent environment "env2"',
            ':3: Environment "env2" has circular parent environment "env"'
        ])
        self.assertListEqual(sorted(environments.keys()), ['env', 'env2', 'env3'])
        self.assertEqual(environments['env'].name, 'env')
        self.assertTupleEqual(environments['env'].parents, ('env2',))
        self.assertListEqual(environments['env'].values, [])
        self.assertEqual(environments['env2'].name, 'env2')
        self.assertTupleEqual(environments['env2'].parents, ('env',))
        self.assertListEqual(environments['env2'].values, [])
        self.assertEqual(environments['env3'].name, 'env3')
        self.assertTupleEqual(environments['env3'].parents, ('env',))
        self.assertListEqual(environments['env3'].values, [])

    def test_check_list_index(self):
        environments = Environments()
        errors = environments.parse('''\
env:
    a.0 = "env a.0"
    b.1 = "env b.1"

env2(env):
    a.1 = "env2 a.1"
    a.3 = "env2 a.3"
''')
        self.assertListEqual(errors, [])
        self.assertListEqual(environments.check(), [
            ':3: Invalid list index "b.1"',
            ':7: Invalid list index "a.3"'
        ])
        self.assertListEqual(sorted(environments.keys()), ['env', 'env2'])
        self.assertEqual(environments['env'].name, 'env')
        self.assertTupleEqual(environments['env'].parents, ())
        self.assertListEqual(environments['env'].values, [
            (('a', 0), 'env a.0', '', 2),
            (('b', 1), 'env b.1', '', 3)
        ])
        self.assertEqual(environments['env2'].name, 'env2')
        self.assertTupleEqual(environments['env2'].parents, ('env',))
        self.assertListEqual(environments['env2'].values, [
            (('a', 1), 'env2 a.1', '', 6),
            (('a', 3), 'env2 a.3', '', 7)
        ])

    def test_asdict(self):
        environments = Environments()
        errors = environments.parse('''\
common:
    a.a = "common a.a"
    a.d = "common a.d"

base(common):
    a.a = "base a.a"
    a.b = "base a.b"
    a.c = "base a.c"
    b.0 = "base b.0"
    b.1 = "base b.1"

base2:
    a.b = "base2 a.b"
    a.c = "base2 a.c"
    a.base2 = "base2 a.base2"

env(base, base2):
    a.b = "env a.b"
    a.env = "env a.env"
    b.1 = "env b.1"
    b.0 = "env b.0"
''')
        self.assertListEqual(errors, [])
        self.assertListEqual(environments.check(), [])
        self.assertDictEqual(environments.asdict('env'), {
            'a': {
                'a': 'base a.a',
                'b': 'env a.b',
                'c': 'base2 a.c',
                'base2': 'base2 a.base2',
                'd': 'common a.d',
                'env': 'env a.env'
            },
            'b': [
                'env b.0',
                'env b.1'
            ]
        })

    def test_asdict_map_map(self):
        environments = Environments()
        errors = environments.parse('''\
env:
    a.b.c = "env a.b.c"
    a.c.c = "env a.c.c"
    a.c.d = "env a.c.d"

env2(env):
    a.b.d = "env2 a.b.d"
    a.c.d = "env2 a.c.d"
    a.c.e = "env2 a.c.e"
    a.d.c = "env2 a.d.c"
''')
        self.assertListEqual(errors, [])
        self.assertListEqual(environments.check(), [])
        self.assertDictEqual(environments.asdict('env'), {
            'a': {
                'b': {
                    'c': 'env a.b.c'
                },
                'c': {
                    'c': 'env a.c.c',
                    'd': 'env a.c.d'
                }
            }
        })
        self.assertDictEqual(environments.asdict('env2'), {
            'a': {
                'b': {
                    'c': 'env a.b.c',
                    'd': 'env2 a.b.d'
                },
                'c': {
                    'c': 'env a.c.c',
                    'd': 'env2 a.c.d',
                    'e': 'env2 a.c.e'
                },
                'd': {
                    'c': 'env2 a.d.c'
                }
            }
        })

    def test_asdict_map_list(self):
        environments = Environments()
        errors = environments.parse('''\
env:
    a.a.0 = "env a.a.0"
    a.b.0 = "env a.b.0"
    a.b.1 = "env a.b.1"

env2(env):
    a.a.1 = "env2 a.a.1"
    a.b.1 = "env2 a.b.1"
    a.b.2 = "env2 a.b.2"
    a.c.0 = "env2 a.c.0"
''')
        self.assertListEqual(errors, [])
        self.assertListEqual(environments.check(), [])
        self.assertDictEqual(environments.asdict('env'), {
            'a': {
                'a': [
                    "env a.a.0"
                ],
                'b': [
                    "env a.b.0",
                    "env a.b.1"
                ]
            }
        })
        self.assertDictEqual(environments.asdict('env2'), {
            'a': {
                'a': [
                    'env a.a.0',
                    'env2 a.a.1'
                ],
                'b': [
                    'env a.b.0',
                    'env2 a.b.1',
                    'env2 a.b.2'
                ],
                'c': [
                    'env2 a.c.0'
                ]
            }
        })

    def test_asdict_list_map(self):
        environments = Environments()
        errors = environments.parse('''\
env:
    a.0.b = "env a.0.b"
    a.1.b = "env a.1.b"
    a.2.b = "env a.2.b"

env2(env):
    a.1.b = "env2 a.1.b"
    a.3.b = "env2 a.3.b"
''')
        self.assertListEqual(errors, [])
        self.assertListEqual(environments.check(), [])
        self.assertDictEqual(environments.asdict('env'), {
            'a': [
                {'b': 'env a.0.b'},
                {'b': 'env a.1.b'},
                {'b': 'env a.2.b'}
            ]
        })
        self.assertDictEqual(environments.asdict('env2'), {
            'a': [
                {'b': 'env a.0.b'},
                {'b': 'env2 a.1.b'},
                {'b': 'env a.2.b'},
                {'b': 'env2 a.3.b'}
            ]
        })

    def test_asdict_list_list(self):
        environments = Environments()
        errors = environments.parse('''\
env:
    a.0.0 = "env a.0.0"
    a.1.0 = "env a.1.0"
    a.2.0 = "env a.2.0"
    a.2.1 = "env a.2.1"

env2(env):
    a.1.0 = "env2 a.1.0"
    a.2.1 = "env2 a.2.1"
    a.2.2 = "env2 a.2.2"
    a.3.0 = "env2 a.3.0"
''')
        self.assertListEqual(errors, [])
        self.assertListEqual(environments.check(), [])
        self.assertDictEqual(environments.asdict('env'), {
            'a': [
                ['env a.0.0'],
                ['env a.1.0'],
                ['env a.2.0', 'env a.2.1']
            ]
        })
        self.assertDictEqual(environments.asdict('env2'), {
            'a': [
                ['env a.0.0'],
                ['env2 a.1.0'],
                ['env a.2.0', 'env2 a.2.1', 'env2 a.2.2'],
                ['env2 a.3.0']
            ]
        })

    def test_asdict_circular(self):
        environments = Environments()
        environment = environments.add_environment('env', ['env2'])
        environment.add_value('a', 'env a')
        environment2 = environments.add_environment('env2', ['env'])
        environment2.add_value('b', 'env2 b')
        self.assertListEqual(sorted(environments.keys()), ['env', 'env2'])
        self.assertDictEqual(environments.asdict('env'), {
            'a': 'env a',
            'b': 'env2 b'
        })
        self.assertDictEqual(environments.asdict('env2'), {
            'a': 'env a',
            'b': 'env2 b'
        })

    def test_asdict_unknown(self):
        environments = Environments()
        environment = environments.add_environment('env', ['env2'])
        environment.add_value('a', 'env a')
        self.assertListEqual(sorted(environments.keys()), ['env'])
        self.assertDictEqual(environments.asdict('env'), {
            'a': 'env a'
        })

    def test_asdict_list_index(self):
        environments = Environments()
        environment = environments.add_environment('env', [])
        environment.add_value('a.0', 'env a.0')
        environment.add_value('a.1', 'env a.1')
        environment.add_value('b.1', 'env b.1')
        self.assertListEqual(sorted(environments.keys()), ['env'])
        self.assertDictEqual(environments.asdict('env'), {
            'a': [
                'env a.0',
                'env a.1'
            ]
        })

    def test_asdict_type_change(self):
        environments = Environments()
        environment = environments.add_environment('env', [])
        environment.add_value('a.0', 'env a.0')
        environment.add_value('a.a', 'env a.a')
        environment.add_value('b.a', 'env b.a')
        environment2 = environments.add_environment('env2', ['env'])
        environment2.add_value('a.a', 'env2 a.a')
        environment2.add_value('b', 'env2 b')
        self.assertListEqual(sorted(environments.keys()), ['env', 'env2'])
        self.assertDictEqual(environments.asdict('env'), {
            'a': [
                'env a.0'
            ],
            'b': {
                'a': 'env b.a'
            }
        })
        self.assertDictEqual(environments.asdict('env2'), {
            'a': [
                'env a.0'
            ],
            'b': {
                'a': 'env b.a'
            }
        })
