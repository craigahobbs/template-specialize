# Copyright (C) 2017-2018 Craig Hobbs
#
# Licensed under the MIT License
# https://github.com/craigahobbs/template-specialize/blob/master/LICENSE

from io import StringIO
import os
import unittest.mock as unittest_mock

from template_specialize import __version__
import template_specialize.__main__
from template_specialize.main import main

from . import TestCase


class TestMain(TestCase):

    def test_module_main(self):
        self.assertTrue(template_specialize.__main__)

    def test_version(self):
        for argv in [
                ['-v'],
                ['--version']
        ]:
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                with self.assertRaises(SystemExit) as cm_exc:
                    main(argv)

            self.assertEqual(cm_exc.exception.code, 0)
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), str(__version__) + '\n')

    def test_missing_src_and_dst(self):
        for argv in [
                [],
                ['src.txt']
        ]:
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                with self.assertRaises(SystemExit) as cm_exc:
                    main(argv)

            self.assertEqual(cm_exc.exception.code, 2)
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(
                stderr.getvalue(),
                '''\
usage: setup.py [-h] [-c FILE] [-e ENV] [--key KEY] [--value VALUE] [-v]
                [SRC] [DST]
setup.py: error: missing source file/directory and/or destination file/directory
'''
            )

    def test_mismatched_keys_values(self):
        for argv in [
                ['--key', 'a', 'src.txt', 'dst.txt'],
                ['--key', 'a', '--value', 'foo', '--key', 'b', 'src.txt', 'dst.txt']
        ]:
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                with self.assertRaises(SystemExit) as cm_exc:
                    main(argv)

            self.assertEqual(cm_exc.exception.code, 2)
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(
                stderr.getvalue(),
                '''\
usage: setup.py [-h] [-c FILE] [-e ENV] [--key KEY] [--value VALUE] [-v]
                [SRC] [DST]
setup.py: error: mismatched keys/values
'''
            )

    def test_sys_argv(self):
        test_files = [
            ('template.txt', 'the value of "foo" is "{{foo}}"')
        ]
        with self.create_test_files(test_files) as input_dir, \
             self.create_test_files([]) as output_dir:
            input_path = os.path.join(input_dir, 'template.txt')
            output_path = os.path.join(output_dir, 'other.txt')
            argv = ['template-specialize', input_path, output_path, '--key', 'foo', '--value', 'bar']
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr, \
                 unittest_mock.patch('sys.argv', argv):
                main()

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            with open(os.path.join(output_dir, 'other.txt'), 'r', encoding='utf-8') as f_output:
                self.assertEqual(f_output.read(), 'the value of "foo" is "bar"')

    def test_environment_only(self):
        test_files = [
            (
                'config1.config',
                '''\
env1:
    a.a = "foo"
    a.c.1 = 2
    a.c.0 = 1

env2:
    b.a = "nope"
'''
            ),
            (
                'config2.config',
                '''\
env3(env1):
    a.b = "bar"
    a.c.2 = 3
'''
            ),
            (
                'template.txt', '''\
a.a = {{a.a}}
a.b = {{a.b}}
a.c = {{a.c}}
'''
            )
        ]
        with self.create_test_files(test_files) as input_dir, \
             self.create_test_files([]) as output_dir:
            config1_path = os.path.join(input_dir, 'config1.config')
            config2_path = os.path.join(input_dir, 'config2.config')
            input_path = os.path.join(input_dir, 'template.txt')
            output_path = os.path.join(output_dir, 'other.txt')
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                main(['-c', config1_path, '-c', config2_path, '-e', 'env3', input_path, output_path])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            with open(os.path.join(output_dir, 'other.txt'), 'r', encoding='utf-8') as f_output:
                self.assertEqual(
                    f_output.read(),
                    '''\
a.a = foo
a.b = bar
a.c = [1, 2, 3]'''
                )

    def test_keys_only(self):
        test_files = [
            (
                'template.txt', '''\
a.a = {{a.a}}
a.b = {{a.b}}
a.c = {{a.c}}
'''
            )
        ]
        with self.create_test_files(test_files) as input_dir, \
             self.create_test_files([]) as output_dir:
            input_path = os.path.join(input_dir, 'template.txt')
            output_path = os.path.join(output_dir, 'other.txt')
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                main([
                    '--key', 'a.a', '--value', 'foo',
                    '--key', 'a.b', '--value', 'bar',
                    '--key', 'a.c.0', '--value', '3',
                    input_path,
                    output_path
                ])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            with open(os.path.join(output_dir, 'other.txt'), 'r', encoding='utf-8') as f_output:
                self.assertEqual(
                    f_output.read(),
                    '''\
a.a = foo
a.b = bar
a.c = [3]'''
                )

    def test_environment_and_keys(self):
        test_files = [
            (
                'config.config',
                '''\
env:
    a.a = "foo"
    a.b = "bar"
    a.c.0 = 1
'''
            ),
            (
                'template.txt', '''\
a.a = {{a.a}}
a.b = {{a.b}}
a.c = {{a.c}}
'''
            )
        ]
        with self.create_test_files(test_files) as input_dir, \
             self.create_test_files([]) as output_dir:
            config_path = os.path.join(input_dir, 'config.config')
            input_path = os.path.join(input_dir, 'template.txt')
            output_path = os.path.join(output_dir, 'other.txt')
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                main([
                    '-c', config_path,
                    '-e', 'env',
                    '--key', 'a.b',
                    '--value', 'bonk',
                    '--key', 'a.c.0',
                    '--value', '10',
                    '--key', 'a.c.1',
                    '--value', '11',
                    input_path,
                    output_path
                ])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            with open(os.path.join(output_dir, 'other.txt'), 'r', encoding='utf-8') as f_output:
                self.assertEqual(
                    f_output.read(),
                    '''\
a.a = foo
a.b = bonk
a.c = [10, 11]'''
                )

    def test_unknown_environment(self):
        test_files = [
            (
                'config.config',
                '''\
env:
    a.a = "foo"
'''
            )
        ]
        with self.create_test_files(test_files) as input_dir:
            config_path = os.path.join(input_dir, 'config.config')
            for argv in [
                    ['-c', config_path, '-e', 'unknown', 'src.txt', 'dst.txt'],
                    ['-e', 'unknown', 'src.txt', 'dst.txt']
            ]:
                with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                     unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                    with self.assertRaises(SystemExit) as cm_exc:
                        main(argv)

                self.assertEqual(cm_exc.exception.code, 2)
                self.assertEqual(stdout.getvalue(), '')
                self.assertEqual(
                    stderr.getvalue(),
                    '''\
usage: setup.py [-h] [-c FILE] [-e ENV] [--key KEY] [--value VALUE] [-v]
                [SRC] [DST]
setup.py: error: unknown environment "unknown"
'''
                )

    def test_file_to_file(self):
        test_files = [
            ('template.txt', 'the value of "foo" is "{{foo}}"')
        ]
        with self.create_test_files(test_files) as input_dir, \
             self.create_test_files([]) as output_dir:
            input_path = os.path.join(input_dir, 'template.txt')
            output_path = os.path.join(output_dir, 'other.txt')
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                main([input_path, output_path, '--key', 'foo', '--value', 'bar'])

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
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                main([input_path, output_path, '--key', 'foo', '--value', 'bar'])

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
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                main([input_dir, output_dir, '--key', 'foo', '--value', 'bar'])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            with open(os.path.join(output_dir, 'template.txt'), 'r', encoding='utf-8') as f_output:
                self.assertEqual(f_output.read(), 'the value of "foo" is "bar"')
            with open(os.path.join(output_dir, 'subdir', 'subtemplate.txt'), 'r', encoding='utf-8') as f_output:
                self.assertEqual(f_output.read(), 'agree, "bar" is the value of "foo"')
