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

    def aws_auth(self):
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
        self.data['cloudformation'] = io_handle.read_file(config_file=resource_data_file)

    def aws_s3(self):
        if 's3' not in self.data:
            self.data['s3'] = dict()
        if 'enable' not in self.data['s3']:
            self.data['s3']['enable'] = False
        if 'bucket' not in self.data['s3']:
            self.data['s3']['bucket'] = None
        aws_region = self.data['aws']['region']

        if self.options.enable_s3:
            if not self.options.s3_bucket:
                self.parser.print_help()
                self.parser.error('An S3 Bucket name must be provided, to store artifacts into')
            self.data['s3']['enable'] = True
            s3_bucket = self.data['s3']['bucket'] = self.options.s3_bucket
            s3_path = self.data['s3']['path'] = f'cfn_stack_rename'
            self.data['s3']['uri'] = f'https://{s3_bucket}.s3.{aws_region}.amazonaws.com/{s3_path}'

    def record_state(self, io_handle, date_stamp):
        state_root = 'state'
        if 'state' not in self.data:
            self.data['state'] = dict()

        self.data['state'] = dict()
        self.data['state']['root'] = state_root
        state_location = self.data['state']['location'] = f'{state_root}/{date_stamp}'
        self.data['state']['date'] = date_stamp
        stack_name = self.data['state']['stack_name'] = self.options.stack_name
        new_stack = self.data['state']['new_stack'] = self.options.new_stack
        self.data['state']['change_set_name'] = f'stack-rename-{date_stamp}'
        self.data['state'][stack_name] = dict()
        self.data['state'][new_stack] = dict()
        self.data['state'][stack_name]['description'] = dict()
        self.data['state'][stack_name]['exports'] = dict()
        self.data['state'][stack_name]['imported_by'] = dict()
        self.data['state'][stack_name]['resources'] = dict()
        self.data['state'][stack_name]['drifts'] = dict()
        self.data['state'][stack_name]['change_set'] = dict()
        self.data['state'][stack_name]['params'] = dict()
        self.data['state'][stack_name]['supported_resources'] = dict()
        self.data['state'][stack_name]['unsupported_resources'] = dict()
        self.data['state'][stack_name]['undriftable_resources'] = dict()

        io_handle.make_dir(path=state_location)

    def read_state(self, io_handle):

        date_stamp = io_handle.read_file('state/current_state.json')['date']
        if self.options.time_stamp:
            date_stamp = self.options.time_stamp

        if not date_stamp:
            self.parser.print_help()
            self.parser.error(f'Date Stamp: {date_stamp} is empty, please provide a correct value')

        state_location = f'state/{date_stamp}'

        if not io_handle.dir_exists(state_location):
            self.parser.print_help()
            self.parser.error(f'Date Stamp: {date_stamp} is not valid {state_location} could not be found')

        state_data = io_handle.read_file(f'{state_location}/state.json')
        return date_stamp, state_data

    def return_data(self):
        return self.data
