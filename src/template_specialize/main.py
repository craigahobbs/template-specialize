# Licensed under the MIT License
# https://github.com/craigahobbs/template-specialize/blob/main/LICENSE

"""
template-specialize command-line script main module
"""

import argparse
from itertools import chain
import os
import shutil
import warnings

import jinja2
import jinja2.ext
import yaml

from .aws_parameter_store import ParameterStoreExtension


def main(argv=None):
    """
    template-specialize command-line script main entry point
    """

    # Command line arguments
    parser = argparse.ArgumentParser(prog='template-specialize')
    parser.add_argument('src_path', metavar='SRC',
                        help='the source template file or directory')
    parser.add_argument('dst_path', metavar='DST',
                        help='the destination file or directory')
    parser.add_argument('-c', dest='environment_files', metavar='FILE', action='append',
                        help='the environment files')
    parser.add_argument('-e', dest='environment', metavar='ENV',
                        help='the environment name')
    parser.add_argument('-k', '--key', action='append', nargs=2, dest='keys', metavar=('KEY', 'VALUE'), default=[],
                        help='add a template key and value')
    parser.add_argument('--dump', action='store_true',
                        help='dump the template variables')
    args = parser.parse_args(args=argv)

    # Parse the environment files
    environments = {}
    if args.environment_files:
        for environment_file in args.environment_files:
            try:
                with open(environment_file, 'r', encoding='utf-8') as f_environment:
                    _parse_environments(f_environment, environments)
            except Exception as exc: # pylint: disable=broad-except
                parser.exit(message=f'{exc}\n', status=2)

    # Build the template variables dict
    template_variables = {}
    try:
        if args.environment is not None:
            _merge_environment(environments, args.environment, template_variables, set())
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', DeprecationWarning)
            for key, value in args.keys:
                _merge_values({key: yaml.full_load(value)}, template_variables)
    except Exception as exc: # pylint: disable=broad-except
        parser.exit(message=f'{exc}\n', status=2)

    # Dump the template variables, if necessary
    if args.dump:
        parser.exit(message=yaml.dump(template_variables, default_flow_style=False))

    # Get the source template file paths
    is_dir = os.path.isdir(args.src_path)
    if is_dir:
        src_dir = args.src_path
        src_files = list(
            os.path.relpath(src_file, src_dir) for src_file in
            chain.from_iterable((os.path.join(root, file_) for file_ in files) for root, _, files in os.walk(args.src_path))
        )
    else:
        src_dir = os.path.dirname(args.src_path)
        src_files = [os.path.basename(args.src_path)]

    # Get the destination template file paths
    if is_dir:
        dst_files = [os.path.join(args.dst_path, src_file) for src_file in src_files]
    else:
        dst_files = [args.dst_path]

    # Template extensions - rename extension is only available for directory destination paths
    extensions = [ParameterStoreExtension]
    if is_dir:
        extensions.append(TemplateSpecializeRenameExtension)

    # Process the template files
    environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(src_dir, encoding='utf-8'),
        extensions=extensions,
        undefined=jinja2.StrictUndefined,
        keep_trailing_newline=True
    )
    for src_file, dst_file in zip(src_files, dst_files):
        try:
            # Load the template
            template = environment.get_template(src_file)

            # Ensure the destination directory exists (only for template directories)
            if is_dir:
                os.makedirs(os.path.dirname(dst_file), exist_ok=True)

            # Render the template
            template.stream(**template_variables).dump(dst_file, encoding='utf-8')
        except jinja2.TemplateNotFound:
            parser.exit(message=f'{os.path.join(src_dir, src_file)}: template file or directory not found\n', status=2)
        except jinja2.TemplateSyntaxError as exc:
            parser.exit(message=f'{exc.filename}:{exc.lineno}: {exc.message}\n', status=2)
        except Exception as exc: # pylint: disable=broad-except
            parser.exit(message=f'{os.path.join(src_dir, src_file)}: error: {exc}\n', status=2)

    # Process any template destination path rename and delete operations
    if is_dir:
        dst_path_norm = os.path.join(os.path.normpath(args.dst_path), '')
        for rename_path_rel, rename_name in environment.template_specialize_rename: # pylint: disable=no-member
            rename_path = os.path.normpath(os.path.join(args.dst_path, rename_path_rel))

            # Ensure the source path is contained by the destination template directory
            if os.path.commonprefix((dst_path_norm, rename_path)) != dst_path_norm:
                parser.exit(message=f'template_specialize_rename invalid path {rename_path_rel!r}', status=2)

            # Delete?
            try:
                if rename_name is None:
                    if os.path.isdir(rename_path):
                        shutil.rmtree(rename_path)
                    else:
                        os.unlink(rename_path)
                else:
                    # If destination is a directory, delete it first
                    rename_dst_path = os.path.join(os.path.dirname(rename_path), rename_name)
                    if os.path.isdir(rename_dst_path) and not os.path.samefile(rename_path, rename_dst_path):
                        shutil.rmtree(rename_dst_path)

                    # Rename...
                    os.rename(rename_path, rename_dst_path)
            except Exception as exc: # pylint: disable=broad-except
                parser.exit(message=f'template_specialize_rename error: {exc}', status=2)


class TemplateSpecializeRenameExtension(jinja2.ext.Extension):
    tags = set(['template_specialize_rename'])

    def __init__(self, environment):
        super().__init__(environment)
        environment.extend(template_specialize_rename=[])

    def parse(self, parser):
        lineno = next(parser.stream).lineno
        path = parser.parse_expression()
        if parser.stream.skip_if('comma'):
            name = parser.parse_expression()
        else:
            name = jinja2.nodes.Const(None)
        result = self.call_method('_rename', [path, name], lineno=lineno)
        return jinja2.nodes.Output([result], lineno=lineno)

    def _rename(self, path, name):
        if isinstance(path, jinja2.Undefined):
            path._fail_with_undefined_error() # pylint: disable=protected-access
        if isinstance(name, jinja2.Undefined):
            name._fail_with_undefined_error() # pylint: disable=protected-access
        if not (isinstance(path, str) and path.strip() != ''):
            raise ValueError(f'template_specialize_rename - invalid source path {path!r}')
        if name is not None and \
           not (isinstance(name, str) and os.path.basename(name).strip() != '' and os.path.dirname(name) == ''):
            raise ValueError(f'template_specialize_rename - invalid destination name {name!r}')
        self.environment.template_specialize_rename.append((path.strip(), name.strip() if name is not None else None))
        return ''


def _parse_environments(environment_yaml, environments):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', DeprecationWarning)
        loaded_environments = yaml.full_load(environment_yaml)
    if not isinstance(loaded_environments, dict):
        raise ValueError(f'invalid environments container: {loaded_environments!r:.100s}')
    for environment_name, environment_info in loaded_environments.items():
        if not isinstance(environment_name, str):
            raise ValueError(f'invalid environment name {environment_name!r:.100s}')
        if environment_name in environments:
            raise ValueError(f'redefinition of environment {environment_name!r:.100s}')
        if not isinstance(environment_info, dict):
            raise ValueError(f'invalid environment metadata for environment {environment_name!r:.100s}: {environment_info!r:.100s}')
        environment_parents = environment_info.get('parents')
        if (environment_parents is not None and not isinstance(environment_parents, list)) or \
           (environment_parents is not None and not all(isinstance(name, str) for name in environment_parents)):
            raise ValueError(f'invalid parents for environment {environment_name!r:.100s}: {environment_parents!r:.100s}')
        environment_values = environment_info.get('values')
        if environment_values is not None and not isinstance(environment_values, dict):
            raise ValueError(f'invalid values for environment {environment_name!r:.100s}: {environment_values!r:.100s}')
        environments[environment_name] = environment_info


def _merge_environment(environments, name, values, visited):
    environment = environments.get(name)
    if environment is None:
        raise ValueError(f'unknown environment {name!r:.100}')
    environment_parents = environment.get('parents')
    if environment_parents is not None:
        for environment_parent in environment_parents:
            if environment_parent in visited:
                raise ValueError(f'circular inheritance with environment {environment_parent!r:.100s}')
            visited.add(environment_parent)
            values = _merge_environment(environments, environment_parent, values, visited)
            visited.remove(environment_parent)
    environment_values = environment.get('values')
    if environment_values is not None:
        values = _merge_values(environment_values, values)
    return values


def _merge_values(src, dst):
    if isinstance(src, list):
        if not isinstance(dst, list):
            dst = []
        len_dst = len(dst)
        for idx, src_value in enumerate(src):
            if idx < len_dst:
                dst[idx] = _merge_values(src_value, dst[idx])
            else:
                dst.append(_merge_values(src_value, None))
        return dst
    if isinstance(src, dict):
        if not isinstance(dst, dict):
            dst = {}
        for key, src_value in src.items():
            dst[key] = _merge_values(src_value, dst.get(key))
        return dst
    return src
