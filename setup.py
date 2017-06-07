# Copyright (C) 2017 Craig Hobbs
#
# Licensed under the MIT License
# https://github.com/craigahobbs/template-specialize/blob/master/LICENSE

from setuptools import setup

TESTS_REQUIRE = []

setup(
    name='template-specialize',
    version='0.1',
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
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        "Topic :: Utilities",
    ],
    packages=['template_specialize'],
    install_requires=[
        'jinja2 >= 2.9',
    ],
    test_suite='template_specialize.tests',
    tests_require=TESTS_REQUIRE,
    extras_require={
        'tests': TESTS_REQUIRE,
    },
    entry_points={
        'console_scripts': ['template-specialize = template_specialize:main'],
    },
)
