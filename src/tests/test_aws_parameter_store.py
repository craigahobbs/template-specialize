# Licensed under the MIT License
# https://github.com/craigahobbs/template-specialize/blob/main/LICENSE

# pylint: disable=missing-class-docstring, missing-function-docstring, missing-module-docstring

import unittest
import unittest.mock as unittest_mock

import botocore.exceptions
from jinja2 import Environment, StrictUndefined
from template_specialize.aws_parameter_store import ParameterStoreExtension


class TestAWSParameterStore(unittest.TestCase):

    @staticmethod
    def _get_parameter(**kwargs):
        return {
            'Parameter': {
                'Value': f'{kwargs["Name"]}-{{value}}'
            }
        }

    def test_aws_parameter_store(self):
        environment = Environment(extensions=[ParameterStoreExtension], undefined=StrictUndefined)
        template = environment.from_string(
            '''\
{% set val = 'val1' -%}
val1 = {% aws_parameter_store 'val1' %}
val2 = {% aws_parameter_store 'val2' %}
again, val1 = {% aws_parameter_store val %}
'''
        )
        with unittest_mock.patch('botocore.session') as mock_session:
            mock_session.get_session.return_value.create_client.return_value.get_parameter.side_effect = self._get_parameter
            self.assertEqual(
                template.render({'val1': 'val1-str', 'val2': 7}),
                '''\
val1 = val1-{value}
val2 = val2-{value}
again, val1 = val1-{value}'''
            )

        self.assertEqual(
            mock_session.get_session.call_args_list,
            [
                unittest_mock.call()
            ]
        )
        self.assertEqual(
            mock_session.get_session.return_value.create_client.call_args_list,
            [
                unittest_mock.call('ssm')
            ]
        )
        self.assertEqual(
            mock_session.get_session.return_value.create_client.return_value.get_parameter.call_args_list,
            [
                unittest_mock.call(Name='val1', WithDecryption=True),
                unittest_mock.call(Name='val2', WithDecryption=True)
            ]
        )

    def test_aws_parameter_store_error(self):
        environment = Environment(extensions=[ParameterStoreExtension], undefined=StrictUndefined)
        template = environment.from_string(
            '''\
val1 = {% aws_parameter_store 'val1' %}
'''
        )
        with unittest_mock.patch('botocore.session') as mock_session:
            mock_session.get_session.return_value.create_client.return_value.get_parameter.side_effect = \
                botocore.exceptions.ClientError({'Error': {'Code': 'SomeError'}}, 'GetParameter')
            with self.assertRaises(ValueError) as cm_exc:
                template.render({'val1': 'val1-str', 'val2': 7})
            self.assertEqual(str(cm_exc.exception), 'Failed to retrieve value "val1" from parameter store with error: SomeError')

        self.assertEqual(
            mock_session.get_session.call_args_list,
            [
                unittest_mock.call()
            ]
        )
        self.assertEqual(
            mock_session.get_session.return_value.create_client.call_args_list,
            [
                unittest_mock.call('ssm')
            ]
        )
        self.assertEqual(
            mock_session.get_session.return_value.create_client.return_value.get_parameter.call_args_list,
            [
                unittest_mock.call(Name='val1', WithDecryption=True)
            ]
        )
