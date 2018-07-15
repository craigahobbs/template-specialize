# Copyright (C) 2017-2018 Craig Hobbs
#
# Licensed under the MIT License
# https://github.com/craigahobbs/template-specialize/blob/master/LICENSE

from io import StringIO
import os
import unittest.mock as unittest_mock

from template_specialize.main import main

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
