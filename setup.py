#!/usr/bin/env python3

from setuptools import setup

setup(
    name='cfn_stack_rename',
    version='0.1',
    description='CloudFormation Stack Rename Tool',
    include_package_data=True,
    packages=['libs'],
    install_requires=[
        "ruamel.yaml>=0.16.0",
        "pyyaml>=5",
    ],
    scripts=[
        'stack_rename',
        'stack_recover',
        'config_convertor',
    ],
    package_data={'libs': ['README.md'], }
)
