# Licensed under the MIT License
# https://github.com/craigahobbs/template-specialize/blob/main/LICENSE

try:
    import botocore.session
    import botocore.exceptions
except ImportError: # pragma: nocover
    pass
from jinja2 import nodes, TemplateRuntimeError
from jinja2.ext import Extension


class ParameterStoreExtension(Extension):
    __slots__ = ()

    tags = set(['aws_parameter_store'])

    def __init__(self, environment):
        super().__init__(environment)
        environment.extend(aws_parameter_store_client=None, aws_parameter_store_values={})

    def parse(self, parser):
        lineno = next(parser.stream).lineno
        name = parser.parse_expression()
        parameter_value = self.call_method('_get_parameter', [name], lineno=lineno)
        return nodes.Output([parameter_value], lineno=lineno)

    def _get_parameter(self, name):
        if name not in self.environment.aws_parameter_store_values:

            # Create the ssm client as needed
            if self.environment.aws_parameter_store_client is None:
                session = botocore.session.get_session()
                self.environment.aws_parameter_store_client = session.create_client('ssm')

            try:
                result = self.environment.aws_parameter_store_client.get_parameter(Name=name, WithDecryption=True)
                self.environment.aws_parameter_store_values[name] = result['Parameter']['Value']
            except botocore.exceptions.ClientError as ex:
                code = ex.response.get('Error', {}).get('Code')
                raise TemplateRuntimeError(f'Failed to retrieve value "{name}" from parameter store with error: {code}') from None

        return self.environment.aws_parameter_store_values[name]
