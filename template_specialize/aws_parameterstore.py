
from jinja2 import nodes
from jinja2.exceptions import TemplateRuntimeError
from jinja2.ext import Extension

try:
    import botocore.session
    import botocore.exceptions
except ImportError: # pragma: nocover
    pass


class ParameterStoreExtension(Extension):
    tags = set(['aws_parameterstore'])

    def __init__(self, environment):
        super(ParameterStoreExtension, self).__init__(environment)

        environment.extend(
            aws_parameterstore_client=None,
            aws_parameterstore_values={}
        )

    def _get_parameter(self, name):
        # Create the ssm client as needed.
        if self.environment.aws_parameterstore_client is None:
            session = botocore.session.get_session()
            self.environment.aws_parameterstore_client = session.create_client('ssm')

        if name not in self.environment.aws_parameterstore_values:
            try:
                result = self.environment.aws_parameterstore_client.get_parameter(
                    Name=name,
                    WithDecryption=True
                )
            except botocore.exceptions.ClientError as ex:
                code = ex.response.get('Error', {}).get('Code')
                raise TemplateRuntimeError(
                    'Failed to retrieve value "{0}" from parameter store with error: {1}'.format(name, code)
                ) from None

            self.environment.aws_parameterstore_values[name] = result['Parameter']['Value']

        return self.environment.aws_parameterstore_values[name]

    def parse(self, parser):
        lineno = next(parser.stream).lineno

        name = parser.parse_expression()

        call_method = self.call_method(
            '_get_parameter',
            [name],
            lineno=lineno,
        )
        return nodes.Output([call_method], lineno=lineno)
