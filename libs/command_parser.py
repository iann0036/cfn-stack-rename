#
##
##########################################################################
#                                                                        #
#       command_parser                                                   #
#                                                                        #
#       (c) Vamegh Hedayati                                              #
#                                                                        #
#       Please see https://github.com/vamegh/pylibs                      #
#                    for License Information                             #
#                             GNU/LGPL                                   #
##########################################################################
##
#
#    This manages command line arguments

import argparse
import os

try:
    from ruamel import yaml
except:
    import yaml


class Commands(object):
    def __init__(self, name='', version='0.0.1', message=''):
        self.name = name
        self.version = version
        self.message = message
        self.parser = argparse.ArgumentParser(prog=self.name,
                                              usage=(f'{self.name} [options]\n'
                                                     f'Version: {self.version}'))
        self.parser.add_argument('--version', action='version', version=self.version)

    def add_aws_auth(self):
        self.parser.add_argument('-L', '--auth', dest='authenticate', required=False, action='store_true',
                                 help='Authentication required, default False')
        self.parser.add_argument('-M', '--mfa', dest='mfa',
                                 help='MFA device id - this should be available in your aws account')
        self.parser.add_argument('-A', '--primary-account', dest='primary_account', default='',
                                 help='Your primary account, this should be your main primary account')
        self.parser.add_argument('-S', '--switch-account', dest='switch_account', default='',
                                 help='AWS Secondary Account number to switch into')
        self.parser.add_argument('-R', '--role-name', dest='role_name', default='',
                                 help='AWS role name, this is used for switching')

    def add_aws_config(self):
        self.parser.add_argument('-r', '--region', required=False, action='store',
                                 help='Specify the aws region, defaults to "eu-west-2"')
        self.parser.add_argument('-p', '--profile', required=False, action='store',
                                 help='Specify the aws profile, defaults to "default"')

    def add_aws_s3(self):
        self.parser.add_argument('-S', '--enable_s3', required=False, action='store_true',
                                 help='s3 required, defaults to False')
        self.parser.add_argument('-B', '--s3_bucket', required=False, action='store',
                                 help='Specify the aws s3 bucket to use')

    def add_config(self):
        base_path = os.getcwd()
        config_file = os.path.join("configs", "config.yaml")
        self.parser.add_argument('-c', '--config', action='store', default=config_file,
                                 help=(f'specify the location of the config file, '
                                       f'defaults to  \'configs/config.yaml\''))

    def add_cloudformation(self):
        self.parser.add_argument('-s', '--stack_name', required=True, action='store',
                                 help='Specify the current cloudformation stack name to import resources from')
        self.parser.add_argument('-n', '--new_stack', required=True, action='store',
                                 help='Specify the new cloudformation stack name')

    def add_output(self):
        self.parser.add_argument("--export", "-e", required=False, action='store_true',
                                 help="This option is required if you are using bash or Linux")
        self.parser.add_argument("--output", "-o", required=False, help="output filename", default=".env")
        self.parser.add_argument("--prefix", "-P", required=False, help="output key prefix", default='')

    def set_options(self):
        options = self.parser.parse_args()
        return options, self.parser
