# Licensed under the MIT License
# https://github.com/craigahobbs/template-specialize/blob/main/LICENSE

import os

from setuptools import setup


def main():
    # Read the readme for use as the long description
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'README.md'), encoding='utf-8') as readme_file:
        long_description = readme_file.read()

    # Do the setup
    setup(
        name='template-specialize',
        description='Command-line tool for rendering Jinja2 templates',
        long_description=long_description,
        long_description_content_type='text/markdown',
        version='1.3.4',
        author='Craig A. Hobbs',
        author_email='craigahobbs@gmail.com',
        keywords='jinja2 template render specialize',
        url='https://github.com/craigahobbs/template-specialize',
        license='MIT',
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Topic :: Utilities'
        ],
        package_dir={'': 'src'},
        packages=['template_specialize'],
        install_requires=[
            'jinja2 >= 2.10',
            'pyyaml >= 5.1'
        ],
        entry_points={
            'console_scripts': [
                'template-specialize = template_specialize.main:main'
            ]
        }
    )


if __name__ == '__main__':
    main()
