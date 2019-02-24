# Licensed under the MIT License
# https://github.com/craigahobbs/template-specialize/blob/master/LICENSE

import os

from setuptools import setup

import template_specialize

TESTS_REQUIRE = [
    'botocore >= 1.0.0'
]

def main():
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'README.md'), encoding='utf-8') as readme_file:
        long_description = readme_file.read()

    setup(
        name='template-specialize',
        long_description=long_description,
        long_description_content_type='text/markdown',
        version=template_specialize.__version__,
        author='Craig Hobbs',
        author_email='craigahobbs@gmail.com',
        description=('Recursive template file specializer.'),
        keywords='template specialize',
        url='https://github.com/craigahobbs/template-specialize',
        license='MIT',
        classifiers=[
            "Environment :: Console",
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            "Topic :: Utilities",
        ],
        packages=['template_specialize'],
        install_requires=[
            'jinja2 >= 2.10',
            'pyyaml >= 3.13'
        ],
        entry_points={
            'console_scripts': ['template-specialize = template_specialize.main:main'],
        },
        test_suite='template_specialize.tests',
        tests_require=TESTS_REQUIRE,
        extras_require={
            'tests': TESTS_REQUIRE
        }
    )

if __name__ == '__main__':
    main()
