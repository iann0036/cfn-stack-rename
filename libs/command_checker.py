#
##
##########################################################################
#                                                                        #
#       command_checker                                                  #
#                                                                        #
#       (c) Vamegh Hedayati                                              #
#                                                                        #
#       Please see https://github.com/vamegh/pylibs                      #
#                    for License Information                             #
#                             GNU/LGPL                                   #
##########################################################################
##
#
#    This verifies command line arguments and handles
#    initialisation and injection of configuration data.

import os
import logging


class CommandCheck(object):
    def __init__(self, options=None, parser=None, config_data=None):
        self.options = options
        self.parser = parser
        self.data = config_data

    def git(self):
        git_base_path = '/tmp/'

        for repo, data in self.data['git']['repos'].items():
            self.data['git']['repos'][repo]['path'] = os.path.join(git_base_path, repo)
            self.data['git']['repos'][repo]['name'] = repo

    def aws(self):
        if 'aws' not in self.data:
            self.data['aws'] = {}
        if 'authenticate' not in self.data['aws']:
            self.data['aws']['authenticate'] = False
        if 'role_arn' not in self.data['aws']:
            self.data['aws']['role_arn'] = None
        if 'mfa_arn' not in self.data['aws']:
            self.data['aws']['mfa_arn'] = None
        if self.options.authenticate:
            if not self.options.switch_account:
                self.parser.print_help()
                self.parser.error('An AWS Secondary Account number must be provided, to switch into')
            if not self.options.primary_account:
                self.parser.print_help()
                self.parser.error('A Primary Account Number must be provided')
            if not self.options.role_name:
                self.parser.print_help()
                self.parser.error('An AWS Role Name must be provided')
            if not self.options.mfa:
                self.parser.print_help()
                self.parser.error('An MFA Device ID Must be provided (Usually your HO Email)')
            self.data['aws']['authenticate'] = True
            self.data['aws']['role_arn'] = f'arn:aws:iam::{self.options.switch_account}:role/{self.options.role_name}'
            self.data['aws']['mfa_arn'] = f'arn:aws:iam::{self.options.primary_account}:mfa/{self.options.mfa}'

            if self.options.profile:
                self.data['aws']['profile'] = self.options.profile
            if self.options.region:
                self.data['aws']['region'] = self.options.region

    def aws_data(self, io_handle):
        if 'resource_identifier_file' not in self.data['configs']:
            raise ValueError("Error no AWS Resource Identifiers File found in configuration")

        resource_data_file = self.data['configs']['resource_identifier_file']
        self.data['cloudformation'] = dict()
        self.data['cloudformation'] = io_handle.read_file(config_file=resource_data_file, file_type='json')

    def return_data(self):
        return self.data
