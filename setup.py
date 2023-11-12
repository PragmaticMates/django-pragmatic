#!/usr/bin/env python
from setuptools import setup, find_packages

from pragmatic import VERSION

setup(
    name='django-pragmatic',
    version=VERSION,
    description='Pragmatic tools and utilities for Django projects',
    long_description=open('README.rst').read(),
    author='Pragmatic Mates',
    author_email='info@pragmaticmates.com',
    maintainer='Pragmatic Mates',
    maintainer_email='info@pragmaticmates.com',
    url='https://github.com/PragmaticMates/django-pragmatic',
    packages=find_packages(),
    include_package_data=True,
    install_requires=('django>=4.2', 'django-filter', 'python-pragmatic'),
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Operating System :: OS Independent',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Framework :: Django',
        'License :: OSI Approved :: BSD License',
        'Development Status :: 3 - Alpha'
    ],
    license='BSD License',
    keywords="django pragmatic tools utils",
)
