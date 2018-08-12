# Copyright (C) 2017-2018 Craig Hobbs
#
# Licensed under the MIT License
# https://github.com/craigahobbs/template-specialize/blob/master/LICENSE

from template_specialize.environment import Environment, Environments

from . import TestCase


class TestEnvironment(TestCase):

    def test_add_value(self):
        environment = Environment('env', ())

        self.assertEqual(
            environment.add_value('a.0.b', 'true'),
            (('a', 0, 'b'), True)
        )
        self.assertEqual(
            environment.add_value('a.1.b', 'false'),
            (('a', 1, 'b'), False)
        )
        self.assertEqual(
            environment.add_value('a.2.b', '"string"'),
            (('a', 2, 'b'), 'string')
        )
        self.assertEqual(
            environment.add_value('a.3.b', '7'),
            (('a', 3, 'b'), 7)
        )
        self.assertEqual(
            environment.add_value('a.4.b', '3.14'),
            (('a', 4, 'b'), 3.14)
        )
        self.assertEqual(
            environment.add_value('a.5.b', 'asdf'),
            (('a', 5, 'b'), 'asdf')
        )
        self.assertIsNone(
            environment.add_value('a.5.b', '11')
        )

        self.assertEqual(environment.name, 'env')
        self.assertTupleEqual(environment.parents, ())
        self.assertDictEqual(environment.values, {
            ('a', 0, 'b'): True,
            ('a', 1, 'b'): False,
            ('a', 2, 'b'): 'string',
            ('a', 3, 'b'): 7,
            ('a', 4, 'b'): 3.14,
            ('a', 5, 'b'): 'asdf'
        })


class TestEnvironments(TestCase):

    def test_add_environment(self):
        environments = Environments()
        environment = environments.add_environment('env', [])
        environment2 = environments.add_environment('env2', ['env'])
        self.assertIsNone(environments.add_environment('env2', []))
        self.assertListEqual(sorted(environments.keys()), ['env', 'env2'])
        self.assertIs(environment, environments['env'])
        self.assertEqual(environment.name, 'env')
        self.assertEqual(environment.parents, [])
        self.assertEqual(environment.values, {})
        self.assertIs(environment2, environments['env2'])
        self.assertEqual(environment2.name, 'env2')
        self.assertEqual(environment2.parents, ['env'])
        self.assertEqual(environment2.values, {})

    def test_parse(self):
        environments = Environments()
        environments.parse('''\
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
        self.assertListEqual(sorted(environments.keys()), ['env1', 'env2'])
        self.assertTupleEqual(environments['env1'].parents, ())
        self.assertDictEqual(environments['env1'].values, {
            ('a', 'a'): 'foo',
            ('a', 'b'): 12,
            ('a', 'c'): 12.5,
            ('a', 'd'): True,
            ('b', 0): 'bonk'
        })
        self.assertTupleEqual(environments['env2'].parents, ())
        self.assertDictEqual(environments['env2'].values, {
            ('a', 'a'): 'bar',
            ('a', 'b'): 19,
            ('a', 'c'): 19.5,
            ('a', 'd'): False,
            ('b', 0): 'thud'
        })

    def test_parse_parent(self):
        environments = Environments()
        environments.parse('''\
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
        self.assertListEqual(sorted(environments.keys()), ['base', 'base2', 'env'])
        self.assertTupleEqual(environments['base'].parents, ())
        self.assertDictEqual(environments['base'].values, {
            ('a', 'a'): 'foo',
            ('a', 'b'): 12
        })
        self.assertTupleEqual(environments['base2'].parents, ())
        self.assertDictEqual(environments['base2'].values, {
            ('b', 'a'): 'thud'
        })
        self.assertTupleEqual(environments['env'].parents, ('base', 'base2'))
        self.assertDictEqual(environments['env'].values, {
            ('a', 'b'): 19,
            ('a', 'c'): 'bar',
            ('a', 'd'): 'env a.d',
            ('a', 'e'): 'env a.e'
        })

    def test_parse_error(self):
        with self.assertRaises(SyntaxError) as exc_cm:
            Environments().parse('''\
env1:
    a.a = "foo"
    a.b = foo
    a.c = 12.5
''')
        self.assertEqual(str(exc_cm.exception), ':3: Syntax error : "    a.b = foo"')

    def test_asdict(self):
        environments = Environments()
        environments.parse('''\
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
    b.2 = "env b.2"
    b.0 = "env b.0"
''')
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
                'base b.1',
                'env b.2'
            ]
        })

    def test_asdict_map_map(self):
        environments = Environments()
        environments.parse('''\
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
        environments.parse('''\
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
        environments.parse('''\
env:
    a.0.b = "env a.0.b"
    a.1.b = "env a.1.b"
    a.2.b = "env a.2.b"

env2(env):
    a.1.b = "env2 a.1.b"
    a.3.b = "env2 a.3.b"
''')
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
        environments.parse('''\
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

    def test_error_inconsistent_environment(self): # pylint: disable=invalid-name
        with self.assertRaises(SyntaxError) as exc:
            Environments().parse('''\
foo:
    a = "foo"

foo(bar):
    b = "bonk"
''')
        self.assertEqual(str(exc.exception), ':4: Redefinition of environment "foo"')

    def test_error_value_redefinition(self):
        with self.assertRaises(SyntaxError) as exc:
            Environments().parse('''\
foo:
    a = "foo"

    # this should error
    a = "bonk"
''')
        self.assertEqual(str(exc.exception), ':5: Redefinition of value "a"')
