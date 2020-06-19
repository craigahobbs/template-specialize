# Licensed under the MIT License
# https://github.com/craigahobbs/template-specialize/blob/master/LICENSE

from io import StringIO
import os
import re
import sys
import unittest.mock as unittest_mock

try:
    import botocore.exceptions
except ImportError: # pragma: nocover
    pass

from template_specialize import __version__
import template_specialize.__main__
from template_specialize.main import main, _parse_environments, _merge_environment, _merge_values

from . import TestCase


class TestMain(TestCase):

    def test_console_script(self):
        console_script_path = os.path.join(os.path.dirname(sys.executable), 'template-specialize')
        self.assertTrue(os.path.isfile(console_script_path))

    def test_module_main(self):
        self.assertTrue(template_specialize.__main__)

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
usage: template-specialize [-h] [-c FILE] [-e ENV] [--key KEY] [--value VALUE]
                           [--dump] [-v]
                           [SRC] [DST]
template-specialize: error: mismatched keys/values
'''
            )

    def test_invalid_keys_values(self):
        with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
             unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
            with self.assertRaises(SystemExit) as cm_exc:
                main(['--key', 'a', '--value', 'a: b: c'])

        self.assertEqual(cm_exc.exception.code, 2)
        self.assertEqual(stdout.getvalue(), '')
        self.assertEqual(
            stderr.getvalue(),
            '''\
mapping values are not allowed here
  in "<unicode string>", line 1, column 5:
    a: b: c
        ^
'''
        )

    def test_config_errors(self):
        test_files = [
            (
                'test.config',
                '''\
env1:
  values:
    a:
      a: "env1 a.a"
    b:
      a: "env1 b.a"
    asdf1

env2:
  values:
    a: ["env2 a.0"]
    asdf2
'''
            ),
            (
                'test2.config',
                '''\
env3:
    parents: [env1, env2]
'''
            ),
            (
                'template.txt',
                '''\
a.a = {{a.a}}
b.a = {{b.a}}
'''
            )
        ]
        with self.create_test_files(test_files) as input_dir, \
             self.create_test_files([]) as output_dir:
            test_path = os.path.join(input_dir, 'test.config')
            test2_path = os.path.join(input_dir, 'test2.config')
            input_path = os.path.join(input_dir, 'template.txt')
            output_path = os.path.join(output_dir, 'other.txt')
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                with self.assertRaises(SystemExit) as cm_exc:
                    main([
                        '-c', test_path,
                        '-c', test2_path,
                        '-e', 'env3',
                        '--key', 'b', '--value', '[b0]',
                        input_path,
                        output_path
                    ])

            self.assertEqual(cm_exc.exception.code, 2)
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(
                re.sub('^.+?test', 'test', stderr.getvalue(), flags=re.MULTILINE),
                '''\
while scanning a simple key
test.config", line 7, column 5
could not find expected ':'
test.config", line 9, column 1
'''
            )
            self.assertFalse(os.path.exists(output_path))

    def test_environment_only(self):
        test_files = [
            (
                'test.config',
                '''\
env1:
  values:
    a:
      a: "foo"
      c: [1, 2]

env2:
  values:
    b:
      a: "nope"
'''
            ),
            (
                'test2.config',
                '''\
env3:
  parents: [env1]
  values:
    a:
      b: "bar"
      c: [4, 5, 3]
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
a.c = [4, 5, 3]'''
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
        with self.create_test_files(test_files) as input_dir, \
             self.create_test_files([]) as output_dir:
            input_path = os.path.join(input_dir, 'template.txt')
            output_path = os.path.join(output_dir, 'other.txt')
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                main([
                    '--key', 'a', '--value', '{a: foo}',
                    '--key', 'a', '--value', '{b: bar}',
                    '--key', 'a', '--value', '{c: [3]}',
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
  values:
    a:
      a: foo
      b: bar
      c: [1]
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
                    '--key', 'a',
                    '--value', '{b: bonk}',
                    '--key', 'a',
                    '--value', '{c: [10]}',
                    '--key', 'a',
                    '--value', '{c: [12, 11]}',
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
a.c = [12, 11]'''
                )

    def test_dump(self):
        test_files = [
            (
                'config.config',
                '''\
env:
  values:
    a:
      a: foo
      b: bar
      c: [1]
'''
            )
        ]
        with self.create_test_files(test_files) as input_dir:
            config_path = os.path.join(input_dir, 'config.config')
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                with self.assertRaises(SystemExit) as cm_exc:
                    main([
                        '-c', config_path,
                        '-e', 'env',
                        '--key', 'a',
                        '--value', '{b: bonk}',
                        '--key', 'a',
                        '--value', '{c: [12, 11]}',
                        '--dump'
                    ])

            self.assertEqual(cm_exc.exception.code, 0)
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '''\
a:
  a: foo
  b: bonk
  c:
  - 12
  - 11
''')

    def test_unknown_environment(self):
        test_files = [
            (
                'config.config',
                '''\
env:
  values:
    a:
      a: foo
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
unknown environment 'unknown'
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

    def test_file_to_stdout(self):
        test_files = [
            ('template.txt', 'the value of "foo" is "{{foo}}"')
        ]
        with self.create_test_files(test_files) as input_dir:
            input_path = os.path.join(input_dir, 'template.txt')
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                main([input_path, '--key', 'foo', '--value', 'bar'])

            self.assertEqual(stdout.getvalue(), 'the value of "foo" is "bar"')
            self.assertEqual(stderr.getvalue(), '')

    def test_stdin_to_stdout(self):
        with unittest_mock.patch('sys.stdin', new=StringIO('the value of "foo" is "{{foo}}"')), \
             unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
             unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
            main(['--key', 'foo', '--value', 'bar'])

        self.assertEqual(stdout.getvalue(), 'the value of "foo" is "bar"')
        self.assertEqual(stderr.getvalue(), '')

    def test_stdin_to_file(self):
        with self.create_test_files([]) as output_dir:
            output_path = os.path.join(output_dir, 'other.txt')
            with unittest_mock.patch('sys.stdin', new=StringIO('the value of "foo" is "{{foo}}"')), \
                 unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                main(['-', output_path, '--key', 'foo', '--value', 'bar'])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            with open(output_path, 'r', encoding='utf-8') as f_output:
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
                with self.assertRaises(SystemExit) as cm_exc:
                    main([input_path, output_path, '--key', 'foo', '--value', 'bar'])

            self.assertEqual(cm_exc.exception.code, 2)
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), "[Errno 21] Is a directory: '{0}'\n".format(output_path))
            self.assertTrue(os.path.isfile(input_path))
            self.assertTrue(os.path.isdir(output_path))

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

    def test_dir_to_file(self):
        test_files = [
            (('subdir', 'template.txt'), 'the value of "foo" is "{{foo}}"'),
            ('other.txt', 'hello')
        ]
        with self.create_test_files(test_files) as input_dir:
            input_path = os.path.join(input_dir, 'subdir')
            output_path = os.path.join(input_dir, 'other.txt')
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                with self.assertRaises(SystemExit) as cm_exc:
                    main([input_path, output_path, '--key', 'foo', '--value', 'bar'])

            self.assertEqual(cm_exc.exception.code, 2)
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), "[Errno 17] File exists: '{0}'\n".format(output_path))
            self.assertTrue(os.path.isdir(input_path))
            self.assertTrue(os.path.isfile(output_path))

    def test_file_not_exist(self):
        with self.create_test_files([]) as input_dir, \
             self.create_test_files([]) as output_dir:
            input_path = os.path.join(input_dir, 'template.txt')
            output_path = os.path.join(output_dir, 'other.txt')
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr:
                with self.assertRaises(SystemExit) as cm_exc:
                    main([input_path, output_path, '--key', 'foo', '--value', 'bar'])

            self.assertEqual(cm_exc.exception.code, 2)
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), "[Errno 2] No such file or directory: '{0}'\n".format(input_path))
            self.assertFalse(os.path.exists(input_path))
            self.assertFalse(os.path.exists(output_path))

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
                    'Value': '{0}-{{value}}'.format(kwargs['Name'])
                }
            }

        with self.create_test_files(test_files) as input_dir:
            input_path = os.path.join(input_dir, 'template.txt')
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr, \
                 unittest_mock.patch('botocore.session') as mock_session:
                mock_session.get_session.return_value.create_client.return_value.get_parameter.side_effect = get_parameter
                main([input_path, '--key', 'foo', '--value', 'a"[bar}'])

            self.assertEqual(
                stdout.getvalue(),
                '''\
"some/string-{value}"
some/string-{value}
a"[bar}-{value}'''
            )
            self.assertEqual(stderr.getvalue(), '')

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

        with self.create_test_files(test_files) as input_dir:
            input_path = os.path.join(input_dir, 'template.txt')
            with unittest_mock.patch('sys.stdout', new=StringIO()) as stdout, \
                 unittest_mock.patch('sys.stderr', new=StringIO()) as stderr, \
                 unittest_mock.patch('botocore.session') as mock_session:
                mock_session.get_session.return_value.create_client.return_value.get_parameter.side_effect = \
                    botocore.exceptions.ClientError({'Error': {'Code': 'SomeError'}}, 'GetParameter')

                with self.assertRaises(SystemExit) as cm_exc:
                    main([input_path])

            self.assertEqual(cm_exc.exception.code, 2)
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(
                stderr.getvalue(),
                '''\
Failed to retrieve value "some/string" from parameter store with error: SomeError
'''
            )


class TestParseEnvironments(TestCase):

    def test_parse_environments(self):
        environments = {}
        _parse_environments(
            StringIO('''\
# This is a comment
env:
    values:
        key: value

env2:
    parents: [env]
    values:
        key: value
'''),
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
                StringIO('''\
[1, 2, 3]
'''),
                environments
            )
        self.assertEqual(str(cm_exc.exception), 'invalid environments container: [1, 2, 3]')
        self.assertDictEqual(environments, {})

    def test_parse_environments_invalid_environment_name(self):
        environments = {}
        with self.assertRaises(ValueError) as cm_exc:
            _parse_environments(
                StringIO('''\
1:
'''),
                environments
            )
        self.assertEqual(str(cm_exc.exception), 'invalid environment name 1')
        self.assertDictEqual(environments, {})

    def test_parse_environments_redefined_environment(self):
        environments = {'env': {}}
        with self.assertRaises(ValueError) as cm_exc:
            _parse_environments(
                StringIO('''\
env:
'''),
                environments
            )
        self.assertEqual(str(cm_exc.exception), "redefinition of environment 'env'")
        self.assertDictEqual(environments, {'env': {}})

    def test_parse_environments_invalid_metadata(self):
        environments = {}
        with self.assertRaises(ValueError) as cm_exc:
            _parse_environments(
                StringIO('''\
env: [1, 2, 3]
'''),
                environments
            )
        self.assertEqual(str(cm_exc.exception), "invalid environment metadata for environment 'env': [1, 2, 3]")
        self.assertDictEqual(environments, {})

    def test_parse_environments_invalid_parents_non_list(self):
        environments = {}
        with self.assertRaises(ValueError) as cm_exc:
            _parse_environments(
                StringIO('''\
env:
  parents: {}
'''),
                environments
            )
        self.assertEqual(str(cm_exc.exception), "invalid parents for environment 'env': {}")
        self.assertDictEqual(environments, {})

    def test_parse_environments_invalid_parents_non_str(self):
        environments = {}
        with self.assertRaises(ValueError) as cm_exc:
            _parse_environments(
                StringIO('''\
env:
  parents: ['env2', 1]
'''),
                environments
            )
        self.assertEqual(str(cm_exc.exception), "invalid parents for environment 'env': ['env2', 1]")
        self.assertDictEqual(environments, {})

    def test_parse_environments_invalid_values(self):
        environments = {}
        with self.assertRaises(ValueError) as cm_exc:
            _parse_environments(
                StringIO('''\
env:
  values: []
'''),
                environments
            )
        self.assertEqual(str(cm_exc.exception), "invalid values for environment 'env': []")
        self.assertDictEqual(environments, {})


class TestMergeEnvironment(TestCase):

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
