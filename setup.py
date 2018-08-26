# Copyright (C) 2017-2018 Craig Hobbs
#
# Licensed under the MIT License
# https://github.com/craigahobbs/template-specialize/blob/master/LICENSE

from setuptools import setup

import template_specialize

setup(
    name='template-specialize',
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
        'Programming Language :: Python :: 3.4',
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
    test_suite='template_specialize.tests'
)
