# Copyright (C) 2017-2018 Craig Hobbs
#
# Licensed under the MIT License
# https://github.com/craigahobbs/template-specialize/blob/master/LICENSE

from template_specialize.environment import Environment

from . import TestCase


class TestEnvironment(TestCase):

    def test_parse(self):
        environments = Environment.parse('''\
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
        self.assertIsNone(environments['env1'].parents)
        self.assertListEqual(environments['env1'].values, [
            (('a', 'a'), 'foo', 'env1'),
            (('a', 'b'), 12, 'env1'),
            (('a', 'c'), 12.5, 'env1'),
            (('a', 'd'), True, 'env1'),
            (('b', 0), 'bonk', 'env1'),
        ])
        self.assertIsNone(environments['env2'].parents)
        self.assertListEqual(environments['env2'].values, [
            (('a', 'a'), 'bar', 'env2'),
            (('a', 'b'), 19, 'env2'),
            (('a', 'c'), 19.5, 'env2'),
            (('a', 'd'), False, 'env2'),
            (('b', 0), 'thud', 'env2'),
        ])

    def test_parse_parent(self):
        environments = Environment.parse('''\
base:
    a.a = "foo"
    a.b = 12

base2:
    b.a = "thud"

env:
    a.d = "env a.d"

env(base, base2):
    a.b = 19
    a.c = "bar"

env:
    a.e = "env a.e"
''')
        self.assertListEqual(sorted(environments.keys()), ['base', 'base2', 'env'])
        self.assertIsNone(environments['base'].parents)
        self.assertListEqual(environments['base'].values, [
            (('a', 'a'), 'foo', 'base'),
            (('a', 'b'), 12, 'base'),
        ])
        self.assertIsNone(environments['base2'].parents)
        self.assertListEqual(environments['base2'].values, [
            (('b', 'a'), 'thud', 'base2'),
        ])
        self.assertListEqual(environments['env'].parents, ['base', 'base2'])
        self.assertListEqual(environments['env'].values, [
            (('a', 'd'), 'env a.d', 'env'),
            (('a', 'b'), 19, 'env'),
            (('a', 'c'), 'bar', 'env'),
            (('a', 'e'), 'env a.e', 'env'),
        ])

    def test_parse_error(self):
        try:
            Environment.parse('''\
env1:
    a.a = "foo"
    a.b = foo
    a.c = 12.5
''')
            self.fail()
        except SyntaxError as exc:
            self.assertEqual(str(exc), ':3: Syntax error : "    a.b = foo"')

    def test_asdict(self):
        environments = Environment.parse('''\
common:
    a.a = "common a.a"
    a.d = "common a.d"

base(common):
    a.a = "base a.a"
    a.b = "base a.b"
    b.0 = "base b.0"
    b.1 = "base b.1"

base2:
    a.b = "base2 a.b"
    a.base2 = "base2 a.base2"

env(base, base2):
    a.b = "env a.b"
    a.env = "env a.env"
    b.1 = "env b.1"
    b.0 = "env b.0"
''')
        self.assertDictEqual(Environment.asdict(environments, 'env', extra_values=[(('foo', 'bar'), 'thud')]), {
            'a': {
                'a': 'base a.a',
                'b': 'env a.b',
                'base2': 'base2 a.base2',
                'd': 'common a.d',
                'env': 'env a.env'
            },
            'b': [
                'env b.0',
                'env b.1'
            ],
            'foo': {
                'bar': 'thud'
            }
        })

    def test_error_inconsistent_environment(self): # pylint: disable=invalid-name
        with self.assertRaises(SyntaxError) as exc:
            Environment.parse('''\
foo:
    a = "foo"

foo(bar):
    b = "bonk"

foo:
    c = "blue"

# this should error
foo(bar, womp):
''')
        self.assertEqual(str(exc.exception), ':11: Inconsistent definition of environment "foo"')

    def test_error_value_redefinition(self):
        with self.assertRaises(SyntaxError) as exc:
            Environment.parse('''\
foo:
    a = "foo"

foo:
    # this should error
    a = "bonk"
''')
        self.assertEqual(str(exc.exception), ':6: Redefinition of value "a"')
