# Copyright (C) 2017-2018 Craig Hobbs
#
# Licensed under the MIT License
# https://github.com/craigahobbs/template-specialize/blob/master/LICENSE

from io import StringIO
import os
import unittest.mock as unittest_mock

from template_specialize import Environment, main

from . import TestCase


class TestMain(TestCase):

    def test_file_to_file(self):
        test_files = [
            ('template.txt', 'the value of "foo" is "{{foo}}"')
        ]
        with self.create_test_files(test_files) as input_dir, \
             self.create_test_files([]) as output_dir:
            input_path = os.path.join(input_dir, 'template.txt')
            output_path = os.path.join(output_dir, 'other.txt')
            sys_argv = ['template-specialize', input_path, output_path, '--key', 'foo', '--value', 'bar']
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr, \
                 unittest_mock.patch('sys.argv', sys_argv):
                main()

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            with open(os.path.join(output_dir, 'other.txt'), 'r', encoding='utf-8') as f_output:
                self.assertEqual(f_output.read(), 'the value of "foo" is "bar"')

    def test_file_to_dir(self):
        test_files = [
            ('template.txt', 'the value of "foo" is "{{foo}}"')
        ]
        with self.create_test_files(test_files) as input_dir, \
             self.create_test_files([]) as output_dir:
            input_path = os.path.join(input_dir, 'template.txt')
            output_path = os.path.join(output_dir, '')
            sys_argv = ['template-specialize', input_path, output_path, '--key', 'foo', '--value', 'bar']
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr, \
                 unittest_mock.patch('sys.argv', sys_argv):
                main()

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            with open(os.path.join(output_dir, 'template.txt'), 'r', encoding='utf-8') as f_output:
                self.assertEqual(f_output.read(), 'the value of "foo" is "bar"')

    def test_dir_to_dir(self):
        test_files = [
            ('template.txt', 'the value of "foo" is "{{foo}}"'),
            (('subdir', 'subtemplate.txt'), 'agree, "{{foo}}" is the value of "foo"')
        ]
        with self.create_test_files(test_files) as input_dir, \
             self.create_test_files([]) as output_dir:
            sys_argv = ['template-specialize', input_dir, output_dir, '--key', 'foo', '--value', 'bar']
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr, \
                 unittest_mock.patch('sys.argv', sys_argv):
                main()

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            with open(os.path.join(output_dir, 'template.txt'), 'r', encoding='utf-8') as f_output:
                self.assertEqual(f_output.read(), 'the value of "foo" is "bar"')
            with open(os.path.join(output_dir, 'subdir', 'subtemplate.txt'), 'r', encoding='utf-8') as f_output:
                self.assertEqual(f_output.read(), 'agree, "bar" is the value of "foo"')


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
