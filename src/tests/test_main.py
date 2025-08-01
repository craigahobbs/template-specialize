# Licensed under the MIT License
# https://github.com/craigahobbs/template-specialize/blob/main/LICENSE

from contextlib import contextmanager
import datetime
from io import StringIO
import os
import platform
import sys
from tempfile import TemporaryDirectory
import unittest
import unittest.mock as unittest_mock

import botocore.exceptions
import template_specialize.__main__
from template_specialize.main import main, _parse_environments, _merge_environment, _merge_values


# Helper context manager to create a list of files in a temporary directory
@contextmanager
def create_test_files(file_defs):
    tempdir = TemporaryDirectory()
    try:
        for path_parts, content in file_defs:
            if isinstance(path_parts, str):
                path_parts = [path_parts]
            path = os.path.join(tempdir.name, *path_parts)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as file_:
                file_.write(content)
        yield tempdir.name
    finally:
        tempdir.cleanup()


# Mock datetime class override
class MockDateTime(datetime.datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2017, 12, 1, 7, 33)


class TestMain(unittest.TestCase):

    def test_console_script(self):
        script_ext = '.exe' if platform.system() == 'Windows' else ''
        console_script_path = os.path.join(os.path.dirname(sys.executable), f'template-specialize{script_ext}')
        self.assertTrue(os.path.isfile(console_script_path))

    def test_module_main(self):
        self.assertTrue(template_specialize.__main__)

    def test_sys_argv(self):
        test_files = [
            ('template.txt', 'the value of "foo" is "{{foo}}"')
        ]
        with create_test_files(test_files) as input_dir, \
             create_test_files([]) as output_dir:
            input_path = os.path.join(input_dir, 'template.txt')
            output_path = os.path.join(output_dir, 'other.txt')
            argv = ['template-specialize', input_path, output_path, '--key', 'foo', 'bar']
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr, \
                 unittest_mock.patch('sys.argv', argv):
                main()

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            with open(os.path.join(output_dir, 'other.txt'), 'r', encoding='utf-8') as f_output:
                self.assertEqual(f_output.read(), 'the value of "foo" is "bar"')

    def test_config_errors(self):
        test_files = [
            (
                'test.config',
                'asdf2'
            ),
            (
                'template.txt',
                '''\
a.a = {{a.a}}
b.a = {{b.a}}
'''
            )
        ]
        with create_test_files(test_files) as input_dir, \
             create_test_files([]) as output_dir:
            test_path = os.path.join(input_dir, 'test.config')
            input_path = os.path.join(input_dir, 'template.txt')
            output_path = os.path.join(output_dir, 'other.txt')
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                with self.assertRaises(SystemExit) as cm_exc:
                    main([
                        '-c', test_path,
                        '-e', 'env3',
                        '--key', 'b', '[b0]',
                        input_path,
                        output_path
                    ])

            self.assertEqual(cm_exc.exception.code, 2)
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(
                stderr.getvalue(),
                '''\
Expecting value: line 1 column 1 (char 0)
'''
            )
            self.assertFalse(os.path.exists(output_path))

    def test_environment_only(self):
        test_files = [
            (
                'test.config',
                '''\
{
    "env1": {
        "values": {
            "a": {
                "a": "foo",
                "c": [1, 2]
            }
        }
    },
    "env2": {
        "values": {
            "b": {
                "a": "nope"
            }
        }
    }
}
'''
            ),
            (
                'test2.config',
                '''\
{
    "env3": {
        "parents": ["env1"],
        "values": {
            "a": {
                "b": "bar",
                "c": [4, 5, 3]
            }
        }
    }
}
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
        with create_test_files(test_files) as input_dir, \
             create_test_files([]) as output_dir:
            test_path = os.path.join(input_dir, 'test.config')
            test2_path = os.path.join(input_dir, 'test2.config')
            input_path = os.path.join(input_dir, 'template.txt')
            output_path = os.path.join(output_dir, 'other.txt')
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                main(['-c', test_path, '-c', test2_path, '-e', 'env3', input_path, output_path])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            with open(os.path.join(output_dir, 'other.txt'), 'r', encoding='utf-8') as f_output:
                self.assertEqual(
                    f_output.read(),
                    '''\
a.a = foo
a.b = bar
a.c = [4, 5, 3]
'''
                )

    def test_keys_only(self):
        test_files = [
            (
                'template.txt',
                '''\
a.a = {{a.a}}
a.b = {{a.b}}
a.c = {{a.c}}
'''
            )
        ]
        with create_test_files(test_files) as input_dir, \
             create_test_files([]) as output_dir:
            input_path = os.path.join(input_dir, 'template.txt')
            output_path = os.path.join(output_dir, 'other.txt')
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                main([
                    '--key', 'a', '{"a": "foo"}',
                    '--key', 'a', '{"b": "bar"}',
                    '--key', 'a', '{"c": [3]}',
                    input_path,
                    output_path
                ])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            with open(output_path, 'r', encoding='utf-8') as f_output:
                self.assertEqual(
                    f_output.read(),
                    '''\
a.a = foo
a.b = bar
a.c = [3]
'''
                )

    def test_environment_and_keys(self):
        test_files = [
            (
                'config.config',
                '''\
{
    "env": {
        "values": {
            "a": {
                "a": "foo",
                "b": "bar",
                "c": [1]
            }
        }
    }
}
'''
            ),
            (
                'template.txt',
                '''\
a.a = {{a.a}}
a.b = {{a.b}}
a.c = {{a.c}}
'''
            )
        ]
        with create_test_files(test_files) as input_dir, \
             create_test_files([]) as output_dir:
            config_path = os.path.join(input_dir, 'config.config')
            input_path = os.path.join(input_dir, 'template.txt')
            output_path = os.path.join(output_dir, 'other.txt')
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                main([
                    '-c', config_path,
                    '-e', 'env',
                    '--key', 'a', '{"b": "bonk"}',
                    '--key', 'a', '{"c": [10]}',
                    '--key', 'a', '{"c": [12, 11]}',
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
a.c = [12, 11]
'''
                )

    def test_dump(self):
        test_files = [
            (
                'config.config',
                '''\
{
    "env": {
        "values": {
            "a": {
                "a": "foo",
                "b": "bar",
                "c": [1]
            }
        }
    }
}
'''
            )
        ]
        with create_test_files(test_files) as input_dir, \
             create_test_files([]) as output_dir:
            input_path = os.path.join(input_dir, 'template.txt')
            output_path = os.path.join(output_dir, 'other.txt')
            config_path = os.path.join(input_dir, 'config.config')
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr, \
                 unittest_mock.patch('template_specialize.main.datetime.datetime', MockDateTime):
                with self.assertRaises(SystemExit) as cm_exc:
                    main([
                        input_path,
                        output_path,
                        '-c', config_path,
                        '-e', 'env',
                        '--key', 'a', '{"b": "bonk"}',
                        '--key', 'a', '{"c": [12, 11]}',
                        '--dump'
                    ])

            self.assertEqual(cm_exc.exception.code, 0)
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '''\
{
    "a": {
        "a": "foo",
        "b": "bonk",
        "c": [
            12,
            11
        ]
    },
    "now": "2017-12-01T07:33:00"
}
''')

    def test_unknown_environment(self):
        test_files = [
            (
                'config.config',
                '''\
{
    "env": {
        "values": {
            "a": {
                "a": "foo"
            }
        }
    }
}
'''
            )
        ]
        with create_test_files(test_files) as input_dir:
            config_path = os.path.join(input_dir, 'config.config')
            for argv in (
                    ['-c', config_path, '-e', 'unknown', 'src.txt', 'dst.txt'],
                    ['-e', 'unknown', 'src.txt', 'dst.txt']
            ):
                with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                     unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                    with self.assertRaises(SystemExit) as cm_exc:
                        main(argv)

                self.assertEqual(cm_exc.exception.code, 2)
                self.assertEqual(stdout.getvalue(), '')
                self.assertEqual(
                    stderr.getvalue(),
                    '''\
unknown environment 'unknown'
'''
                )

    def test_file_to_file(self):
        test_files = [
            ('template.txt', 'the value of "foo" is "{{foo}}"')
        ]
        with create_test_files(test_files) as input_dir, \
             create_test_files([]) as output_dir:
            input_path = os.path.join(input_dir, 'template.txt')
            output_path = os.path.join(output_dir, 'other.txt')
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                main([input_path, output_path, '--key', 'foo', 'bar'])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            with open(os.path.join(output_dir, 'other.txt'), 'r', encoding='utf-8') as f_output:
                self.assertEqual(f_output.read(), 'the value of "foo" is "bar"')

    def test_file_to_file_builtins(self):
        test_files = [
            ('template.txt', 'the year is {{now.year}}')
        ]
        with create_test_files(test_files) as input_dir, \
             create_test_files([]) as output_dir:
            input_path = os.path.join(input_dir, 'template.txt')
            output_path = os.path.join(output_dir, 'other.txt')
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr, \
                 unittest_mock.patch('template_specialize.main.datetime.datetime', MockDateTime):
                main([input_path, output_path])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            with open(os.path.join(output_dir, 'other.txt'), 'r', encoding='utf-8') as f_output:
                self.assertEqual(f_output.read(), 'the year is 2017')

    def test_file_to_file_searchpath(self):
        test_files = [
            (('pri', 'template.txt'), "{% include 'sub/year.txt' %}"),
            (('sub', 'year.txt'), 'YYYY')
        ]
        with create_test_files(test_files) as input_dir, \
             create_test_files([]) as output_dir:
            input_path = os.path.join(input_dir, 'pri', 'template.txt')
            output_path = os.path.join(output_dir, 'other.txt')
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr, \
                 unittest_mock.patch('template_specialize.main.datetime.datetime', MockDateTime):
                main([input_path, output_path, '-i', input_dir])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            with open(os.path.join(output_dir, 'other.txt'), 'r', encoding='utf-8') as f_output:
                self.assertEqual(f_output.read(), 'YYYY')

    def test_file_to_dir(self):
        test_files = [
            ('template.txt', 'the value of "foo" is "{{foo}}"')
        ]
        with create_test_files(test_files) as input_dir, \
             create_test_files([]) as output_dir:
            input_path = os.path.join(input_dir, 'template.txt')
            output_path = os.path.join(output_dir, '')
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                with self.assertRaises(SystemExit) as cm_exc:
                    main([input_path, output_path, '--key', 'foo', 'bar'])

            self.assertEqual(cm_exc.exception.code, 2)
            self.assertEqual(stdout.getvalue(), '')
            self.assertTrue(stderr.getvalue().startswith(f'{input_path}: error: '))
            self.assertTrue(stderr.getvalue().endswith(f": {output_path!r}\n"))
            self.assertTrue(os.path.isfile(input_path))
            self.assertTrue(os.path.isdir(output_path))

    def test_dir_to_dir(self):
        test_files = [
            ('template.txt', 'the value of "foo" is "{{foo}}"'),
            (('subdir', 'subtemplate.txt'), 'agree, "{{foo}}" is the value of "foo"')
        ]
        with create_test_files(test_files) as input_dir, \
             create_test_files([]) as output_dir:
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                main([input_dir, output_dir, '--key', 'foo', 'bar'])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            with open(os.path.join(output_dir, 'template.txt'), 'r', encoding='utf-8') as f_output:
                self.assertEqual(f_output.read(), 'the value of "foo" is "bar"')
            with open(os.path.join(output_dir, 'subdir', 'subtemplate.txt'), 'r', encoding='utf-8') as f_output:
                self.assertEqual(f_output.read(), 'agree, "bar" is the value of "foo"')

    def test_dir_to_file(self):
        test_files = [
            (('subdir', 'template.txt'), 'the value of "foo" is "{{foo}}"'),
            ('other.txt', 'hello')
        ]
        with create_test_files(test_files) as input_dir:
            input_path = os.path.join(input_dir, 'subdir')
            output_path = os.path.join(input_dir, 'other.txt')
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                with self.assertRaises(SystemExit) as cm_exc:
                    main([input_path, output_path, '--key', 'foo', 'bar'])

            self.assertEqual(cm_exc.exception.code, 2)
            self.assertEqual(stdout.getvalue(), '')
            self.assertTrue(stderr.getvalue().startswith(f"{os.path.join(input_path, 'template.txt')}: error: "))
            self.assertTrue(stderr.getvalue().endswith(f": {output_path!r}\n"))
            self.assertTrue(os.path.isdir(input_path))
            self.assertTrue(os.path.isfile(output_path))

    def test_file_not_exist(self):
        with create_test_files([]) as input_dir, \
             create_test_files([]) as output_dir:
            input_path = os.path.join(input_dir, 'template.txt')
            output_path = os.path.join(output_dir, 'other.txt')
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                with self.assertRaises(SystemExit) as cm_exc:
                    main([input_path, output_path])

            self.assertEqual(cm_exc.exception.code, 2)
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), f"'template.txt' not found in search path: {input_dir!r}\n")
            self.assertFalse(os.path.exists(input_path))
            self.assertFalse(os.path.exists(output_path))

    def test_rename(self):
        test_files = [
            (
                'template.txt',
                '''\
{# Delete template.txt #}
{% template_specialize_rename "template.txt" %}

{# Rename the file and the sub-directory #}
{% template_specialize_rename "subdir/subtemplate.txt", "newtemplate.txt" %}
{% template_specialize_rename "subdir", "newdir" %}
'''
            ),
            (('subdir', 'subtemplate.txt'), 'agree, "{{foo}}" is the value of "foo"')
        ]
        with create_test_files(test_files) as input_dir, \
             create_test_files([]) as output_dir:
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                main([input_dir, output_dir, '--key', 'foo', 'bar'])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            self.assertFalse(os.path.exists(os.path.join(output_dir, 'template.txt')))
            self.assertFalse(os.path.exists(os.path.join(output_dir, 'subdir')))
            with open(os.path.join(output_dir, 'newdir', 'newtemplate.txt'), 'r', encoding='utf-8') as f_output:
                self.assertEqual(f_output.read(), 'agree, "bar" is the value of "foo"')

    def test_rename_directory_exists(self):
        test_files = [
            (
                'template.txt',
                '''\
{# Delete template.txt #}
{% template_specialize_rename "template.txt" %}

{# Rename the file and the sub-directory #}
{% template_specialize_rename "subdir", "newdir" %}
'''
            ),
            (('subdir', 'subtemplate.txt'), 'agree, "{{foo}}" is the value of "foo"')
        ]
        with create_test_files(test_files) as input_dir, \
             create_test_files([]) as output_dir:
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:

                # Destination directory exists and is non-empty
                os.mkdir(os.path.join(output_dir, 'newdir'))
                os.mkdir(os.path.join(output_dir, 'newdir', 'newsubdir'))

                main([input_dir, output_dir, '--key', 'foo', 'bar'])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            self.assertFalse(os.path.exists(os.path.join(output_dir, 'template.txt')))
            self.assertFalse(os.path.exists(os.path.join(output_dir, 'subdir')))
            with open(os.path.join(output_dir, 'newdir', 'subtemplate.txt'), 'r', encoding='utf-8') as f_output:
                self.assertEqual(f_output.read(), 'agree, "bar" is the value of "foo"')

    def test_rename_unchanged(self):
        test_files = [
            (
                'template.txt',
                '''\
{# Delete template.txt #}
{% template_specialize_rename "template.txt" %}

{# Rename the file and the sub-directory #}
{% template_specialize_rename "subdir/subtemplate.txt", "subtemplate.txt" %}
{% template_specialize_rename "subdir", "subdir" %}
'''
            ),
            (('subdir', 'subtemplate.txt'), 'agree, "{{foo}}" is the value of "foo"')
        ]
        with create_test_files(test_files) as input_dir, \
             create_test_files([]) as output_dir:
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:

                # Destination directory exists and is non-empty
                os.mkdir(os.path.join(output_dir, 'newdir'))
                os.mkdir(os.path.join(output_dir, 'newdir', 'newsubdir'))

                main([input_dir, output_dir, '--key', 'foo', 'bar'])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            self.assertFalse(os.path.exists(os.path.join(output_dir, 'template.txt')))
            self.assertTrue(os.path.exists(os.path.join(output_dir, 'subdir')))
            with open(os.path.join(output_dir, 'subdir', 'subtemplate.txt'), 'r', encoding='utf-8') as f_output:
                self.assertEqual(f_output.read(), 'agree, "bar" is the value of "foo"')

    def test_delete_directory(self):
        test_files = [
            (
                'template.txt',
                '''\
{# Delete template.txt #}
{% template_specialize_rename "template.txt" %}

{# Delete the sub-directory #}
{% template_specialize_rename "subdir" %}
'''
            ),
            (('subdir', 'subtemplate.txt'), 'agree, "{{foo}}" is the value of "foo"')
        ]
        with create_test_files(test_files) as input_dir, \
             create_test_files([]) as output_dir:
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                main([input_dir, output_dir, '--key', 'foo', 'bar'])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            self.assertFalse(os.path.exists(os.path.join(output_dir, 'template.txt')))
            self.assertFalse(os.path.exists(os.path.join(output_dir, 'subdir')))

    def test_rename_error_not_found(self):
        test_files = [
            (
                'template.txt',
                '''\
{% template_specialize_rename 'missing.txt', 'bar.txt' %}
'''
            )
        ]
        with create_test_files(test_files) as input_dir, \
             create_test_files([]) as output_dir:
            output_missing = os.path.join(output_dir, 'missing.txt')
            output_bar = os.path.join(output_dir, 'bar.txt')
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                with self.assertRaises(SystemExit):
                    main([input_dir, output_dir])

            self.assertEqual(stdout.getvalue(), '')
            self.assertTrue(stderr.getvalue().startswith('template_specialize_rename error: '))
            self.assertTrue(stderr.getvalue().endswith(f': {output_missing!r} -> {output_bar!r}'))

    def test_rename_error_no_args(self):
        test_files = [
            (
                'template.txt',
                '''\
{% template_specialize_rename %}
'''
            )
        ]
        with create_test_files(test_files) as input_dir, \
             create_test_files([]) as output_dir:
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                with self.assertRaises(SystemExit):
                    main([input_dir, output_dir])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), f"{os.path.join(input_dir, 'template.txt')}:1: unexpected 'end of statement block'\n")

    def test_rename_error_extra_args(self):
        test_files = [
            (
                'template.txt',
                '''\
{% template_specialize_rename 'template.txt', 'bar.txt, 'extra' %}
'''
            )
        ]
        with create_test_files(test_files) as input_dir, \
             create_test_files([]) as output_dir:
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                with self.assertRaises(SystemExit):
                    main([input_dir, output_dir])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(
                stderr.getvalue(),
                f"{os.path.join(input_dir, 'template.txt')}:1: expected token 'end of statement block', got 'extra'\n"
            )

    def test_rename_error_path_non_str(self):
        test_files = [
            (
                'template.txt',
                '''\
{% template_specialize_rename 7, 'foo.txt' %}
'''
            )
        ]
        with create_test_files(test_files) as input_dir, \
             create_test_files([]) as output_dir:
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                with self.assertRaises(SystemExit):
                    main([input_dir, output_dir])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(
                stderr.getvalue(),
                f"{os.path.join(input_dir, 'template.txt')}: error: template_specialize_rename - invalid source path 7\n"
            )

    def test_rename_error_path_empty(self):
        test_files = [
            (
                'template.txt',
                '''\
{% template_specialize_rename '  ', 'foo.txt' %}
'''
            )
        ]
        with create_test_files(test_files) as input_dir, \
             create_test_files([]) as output_dir:
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                with self.assertRaises(SystemExit):
                    main([input_dir, output_dir])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(
                stderr.getvalue(),
                f"{os.path.join(input_dir, 'template.txt')}: error: template_specialize_rename - invalid source path '  '\n"
            )

    def test_rename_error_path_invalid(self):
        test_files = [
            (
                'template.txt',
                '''\
{% template_specialize_rename '../bar.txt', 'foo.txt' %}
'''
            )
        ]
        with create_test_files(test_files) as input_dir, \
             create_test_files([]) as output_dir:
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                with self.assertRaises(SystemExit):
                    main([input_dir, output_dir])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), f'''\
template_specialize_rename invalid path {os.path.join('..', 'bar.txt')!r}''')

    def test_rename_error_name_non_str(self):
        test_files = [
            (
                'template.txt',
                '''\
{% template_specialize_rename "template.txt", 7 %}
'''
            )
        ]
        with create_test_files(test_files) as input_dir, \
             create_test_files([]) as output_dir:
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                with self.assertRaises(SystemExit):
                    main([input_dir, output_dir])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(
                stderr.getvalue(),
                f"{os.path.join(input_dir, 'template.txt')}: error: template_specialize_rename - invalid destination name 7\n"
            )

    def test_rename_error_name_empty(self):
        test_files = [
            (
                'template.txt',
                '''\
{% template_specialize_rename "template.txt", '  ' %}
'''
            )
        ]
        with create_test_files(test_files) as input_dir, \
             create_test_files([]) as output_dir:
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                with self.assertRaises(SystemExit):
                    main([input_dir, output_dir])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(
                stderr.getvalue(),
                f"{os.path.join(input_dir, 'template.txt')}: error: template_specialize_rename - invalid destination name '  '\n"
            )

    def test_rename_error_name_dirname(self):
        test_files = [
            (
                'template.txt',
                '''\
{% template_specialize_rename "template.txt", '  /foo.txt' %}
'''
            )
        ]
        with create_test_files(test_files) as input_dir, \
             create_test_files([]) as output_dir:
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                with self.assertRaises(SystemExit):
                    main([input_dir, output_dir])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(
                stderr.getvalue(),
                f"{os.path.join(input_dir, 'template.txt')}: error: template_specialize_rename - " + \
                    f"invalid destination name {os.path.join('  ', 'foo.txt')!r}\n"
            )

    def test_rename_error_src_undefined(self):
        test_files = [
            (
                'template.txt',
                '''\
{% template_specialize_rename foobar, "template.txt" %}
'''
            )
        ]
        with create_test_files(test_files) as input_dir, \
             create_test_files([]) as output_dir:
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                with self.assertRaises(SystemExit):
                    main([input_dir, output_dir])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(
                stderr.getvalue(),
                f"{os.path.join(input_dir, 'template.txt')}: error: 'foobar' is undefined\n"
            )

    def test_rename_error_dst_undefined(self):
        test_files = [
            (
                'template.txt',
                '''\
{% template_specialize_rename "template.txt", foobar %}
'''
            )
        ]
        with create_test_files(test_files) as input_dir, \
             create_test_files([]) as output_dir:
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                with self.assertRaises(SystemExit):
                    main([input_dir, output_dir])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(
                stderr.getvalue(),
                f"{os.path.join(input_dir, 'template.txt')}: error: 'foobar' is undefined\n"
            )

    def test_aws_parameter_store(self):
        test_files = [
            (
                'template.txt',
                '''\
{% filter tojson %}{% aws_parameter_store 'some/string' %}{% endfilter %}
{% aws_parameter_store 'some/string' %}
{% aws_parameter_store foo %}
'''
            )
        ]

        def get_parameter(**kwargs):
            return {
                'Parameter': {
                    'Value': f'{kwargs["Name"]}-{{value}}'
                }
            }

        with create_test_files(test_files) as input_dir, \
             create_test_files([]) as output_dir:
            input_path = os.path.join(input_dir, 'template.txt')
            output_path = os.path.join(output_dir, 'other.txt')
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr, \
                 unittest_mock.patch('botocore.session') as mock_session:
                mock_session.get_session.return_value.create_client.return_value.get_parameter.side_effect = get_parameter
                main([input_path, output_path, '--key', 'foo', 'a"[bar}'])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')

            with open(output_path, 'r', encoding='utf-8') as f_output:
                self.assertEqual(
                    f_output.read(),
                    '''\
"some/string-{value}"
some/string-{value}
a"[bar}-{value}
'''
                )

            # get_parameter results should be cached between blocks.
            mock_session.get_session.return_value.create_client.return_value.assert_has_calls([
                unittest_mock.call.get_parameter(Name='some/string', WithDecryption=True),
                unittest_mock.call.get_parameter(Name='a"[bar}', WithDecryption=True)
            ])

    def test_aws_parameter_store_error(self):
        test_files = [
            (
                'template.txt',
                '''\
{% aws_parameter_store 'some/string' %}
'''
            )
        ]

        with create_test_files(test_files) as input_dir, \
             create_test_files([]) as output_dir:
            input_path = os.path.join(input_dir, 'template.txt')
            output_path = os.path.join(output_dir, 'other.txt')
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr, \
                 unittest_mock.patch('botocore.session') as mock_session:
                mock_session.get_session.return_value.create_client.return_value.get_parameter.side_effect = \
                    botocore.exceptions.ClientError({'Error': {'Code': 'SomeError'}}, 'GetParameter')

                with self.assertRaises(SystemExit) as cm_exc:
                    main([input_path, output_path])

            self.assertEqual(cm_exc.exception.code, 2)
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(
                stderr.getvalue(),
                f'{input_path}: error: Failed to retrieve value "some/string" from parameter store with error: SomeError\n'
            )


class TestParseEnvironments(unittest.TestCase):

    def test_parse_environments(self):
        environments = {}
        _parse_environments(
            '''\
// This is a comment
{
    // This is another comment
    "env": {
        "values": {
            "key": "value"
        }
    },
    "env2": {
        "parents": ["env"],
        "values": {
            "key": "value"
        }
    }
}
''',
            environments
        )
        self.assertDictEqual(environments, {
            'env': {
                'values': {
                    'key': 'value'
                }
            },
            'env2': {
                'parents': ['env'],
                'values': {
                    'key': 'value'
                }
            }
        })

    def test_parse_environments_not_dict(self):
        environments = {}
        with self.assertRaises(ValueError) as cm_exc:
            _parse_environments(
                '''\
[1, 2, 3]
''',
                environments
            )
        self.assertEqual(str(cm_exc.exception), 'invalid environments container: [1, 2, 3]')
        self.assertDictEqual(environments, {})

    def test_parse_environments_redefined_environment(self):
        environments = {'env': {}}
        with self.assertRaises(ValueError) as cm_exc:
            _parse_environments(
                '''\
{
    "env": {}
}
''',
                environments
            )
        self.assertEqual(str(cm_exc.exception), "redefinition of environment 'env'")
        self.assertDictEqual(environments, {'env': {}})

    def test_parse_environments_invalid_metadata(self):
        environments = {}
        with self.assertRaises(ValueError) as cm_exc:
            _parse_environments(
                '''\
{
    "env": [1, 2, 3]
}
''',
                environments
            )
        self.assertEqual(str(cm_exc.exception), "invalid environment metadata for environment 'env': [1, 2, 3]")
        self.assertDictEqual(environments, {})

    def test_parse_environments_invalid_parents_non_list(self):
        environments = {}
        with self.assertRaises(ValueError) as cm_exc:
            _parse_environments(
                '''\
{
    "env": {
        "parents": {}
    }
}
''',
                environments
            )
        self.assertEqual(str(cm_exc.exception), "invalid parents for environment 'env': {}")
        self.assertDictEqual(environments, {})

    def test_parse_environments_invalid_parents_non_str(self):
        environments = {}
        with self.assertRaises(ValueError) as cm_exc:
            _parse_environments(
                '''\
{
    "env": {
        "parents": ["env2", 1]
    }
}
''',
                environments
            )
        self.assertEqual(str(cm_exc.exception), "invalid parents for environment 'env': ['env2', 1]")
        self.assertDictEqual(environments, {})

    def test_parse_environments_invalid_values(self):
        environments = {}
        with self.assertRaises(ValueError) as cm_exc:
            _parse_environments(
                '''\
{
    "env": {
        "values": []
    }
}
''',
                environments
            )
        self.assertEqual(str(cm_exc.exception), "invalid values for environment 'env': []")
        self.assertDictEqual(environments, {})


class TestMergeEnvironment(unittest.TestCase):

    def test_merge_environment(self):
        environments = {
            'env': {
                'values': {
                    'a': 1,
                    'b': 2,
                    'c': [{'a': 'b'}]
                }
            },
            'env2': {
                'parents': ['env'],
                'values': {
                    'a': 3,
                    'c': [{'a', 'b2'}, {'c': 'd'}],
                    'd': 4
                }
            },
            'env3': {
                'parents': ['env', 'env2'],
                'values': {
                    'c': [{'c': 'd3'}],
                    'e': 5
                }
            },
            'env4': {
                'parents': ['env3']
            }
        }

        values = _merge_environment(environments, 'env', None, set())
        self.assertDictEqual(values, {
            'a': 1,
            'b': 2,
            'c': [{'a': 'b'}]
        })

        values = {}
        values2 = _merge_environment(environments, 'env2', values, set())
        self.assertIs(values2, values)
        self.assertDictEqual(values, {
            'a': 3,
            'b': 2,
            'c': [{'b2', 'a'}, {'c': 'd'}],
            'd': 4
        })

        values = {}
        values2 = _merge_environment(environments, 'env3', values, set())
        self.assertIs(values2, values)
        self.assertDictEqual(values, {
            'a': 3,
            'b': 2,
            'c': [{'c': 'd3'}, {'c': 'd'}],
            'd': 4,
            'e': 5
        })

        values = {}
        values2 = _merge_environment(environments, 'env4', values, set())
        self.assertIs(values2, values)
        self.assertDictEqual(values, {
            'a': 3,
            'b': 2,
            'c': [{'c': 'd3'}, {'c': 'd'}],
            'd': 4,
            'e': 5
        })

    def test_merge_environment_unknown(self):
        environments = {
            'env': {
                'parents': ['unknown']
            }
        }
        with self.assertRaises(ValueError) as cm_exc:
            _merge_environment(environments, 'env2', None, set())
        self.assertEqual(str(cm_exc.exception), "unknown environment 'env2'")
        with self.assertRaises(ValueError) as cm_exc:
            _merge_environment(environments, 'env', None, set())
        self.assertEqual(str(cm_exc.exception), "unknown environment 'unknown'")

    def test_merge_environment_circular(self):
        environments = {
            'env': {
                'parents': ['env'],
                'values': {
                    'a': 1,
                    'b': 2,
                    'c': [{'a': 'b'}]
                }
            }
        }
        with self.assertRaises(ValueError) as cm_exc:
            _merge_environment(environments, 'env', None, set())
        self.assertEqual(str(cm_exc.exception), "circular inheritance with environment 'env'")

    def test_merge_values(self):
        values = {}
        values2 = _merge_values({
            'a': 'b',
            'b': [1, 2, 3],
            'c': {'a': 'b', 'c': 'd'},
            'd': [{'a': 'b'}, {'c': 'd'}],
            'e': {'a': [1, 2, 3], 'b': [4, 5, 6]},
            'f': 1
        }, values)
        self.assertIs(values, values2)
        self.assertDictEqual(values, {
            'a': 'b',
            'b': [1, 2, 3],
            'c': {'a': 'b', 'c': 'd'},
            'd': [{'a': 'b'}, {'c': 'd'}],
            'e': {'a': [1, 2, 3], 'b': [4, 5, 6]},
            'f': 1
        })

        values2 = _merge_values({
            'a': 'b2',
            'b': [4, 5],
            'c': {'a': 'b2', 'e': 'f'},
            'd': [{'e': 'f'}, {'c': 'd2'}, {'g': 'h'}],
            'e': {'a': [4, 5], 'b': [7, 8, 9, 10]},
            'g': 2
        }, values)
        self.assertIs(values, values2)
        self.assertDictEqual(values, {
            'a': 'b2',
            'b': [4, 5, 3],
            'c': {'a': 'b2', 'c': 'd', 'e': 'f'},
            'd': [{'a': 'b', 'e': 'f'}, {'c': 'd2'}, {'g': 'h'}],
            'e': {'a': [4, 5, 3], 'b': [7, 8, 9, 10]},
            'f': 1,
            'g': 2
        })

        values2 = _merge_values({
            'a': [1, 2, 3],
            'f': {'a': 'b'},
            'b': 3,
            'd': {'c': 'd'},
            'c': 4,
            'e': [4, 5, 6]
        }, values)
        self.assertIs(values, values2)
        self.assertDictEqual(values, {
            'a': [1, 2, 3],
            'b': 3,
            'c': 4,
            'd': {'c': 'd'},
            'e': [4, 5, 6],
            'f': {'a': 'b'},
            'g': 2
        })
