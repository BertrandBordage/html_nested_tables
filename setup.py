#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals
from distutils.core import setup
from html_nested_tables import VERSION


setup(
    name='html_nested_tables',
    version=VERSION,
    packages=[b'html_nested_tables'],
    url='https://github.com/BertrandBordage/html_nested_tables',
    license='BSD License',
    author='Bertrand Bordage',
    author_email='bordage.bertrand@gmail.com',
    description='Python module that generates nested HTML tables '
                'from nested association lists.',
    long_description=open('README.rst').read(),
)
