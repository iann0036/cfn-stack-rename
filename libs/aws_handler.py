#
##
##########################################################################
#                                                                        #
#       aws_handler                                                      #
#                                                                        #
#       (c) Vamegh Hedayati                                              #
#                                                                        #
#       Please see https://github.com/vamegh/pylibs                      #
#                    for License Information                             #
#                             GNU/LGPL                                   #
##########################################################################
##
#
#  aws_handler - This handles various aws functions

import base64
import time

import boto3
import json
import logging
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound


# yaml config data expected structure:
#
# aws:
#   region: 'eu-west-2'
#   profile: 'default'
#   authenticate: false / true
#   role_arn: <arn_of_role_to_assume> (optional)
#   mfa_arn: <arn_of_mfa usually located on primary account> (optional)

class AWS(object):
    def __init__(self, data=None):
        self.data = data
        self.session = None
        self.client = None

    def login(self):
        aws_profile = None
        if 'profile' in self.data['aws']:
            aws_profile = self.data['aws']['profile']

        if self.data['aws']['authenticate']:
            # auth is handled by this library - via assume role function
            self.session = self.get_assume_role_session(profile=aws_profile)
        else:
            # auth is handled separately ie via saml2aws or aws-vault or  existing ~/.aws/credentials
            self.session = self.get_session(profile=aws_profile)

        if not self.session:
            logging.error(f"Sorry you do not have your aws credentials configured\n"
                          f"Please configure this first, these are stored in ~/.aws/credentials. "
                          f"Please provide the correct profile name to use, if different from 'default'")
            raise ValueError('AWS Profile Not Found')

    def get_session(self, profile=None):
        aws_region = self.data['aws']['region']
        if not profile:
            return boto3.session.Session(region_name=aws_region)

        return boto3.session.Session(profile_name=profile,
                                     region_name=aws_region)

    def get_assume_role_session(self, profile=None):
        aws_region = self.data['aws']['region']
        aws_role_arn = self.data['aws']['role_arn']
        aws_mfa_arn = self.data['aws']['mfa_arn']

        sts_default_provider_chain = boto3.client('sts')
        # Prompt for MFA time-based one-time password (TOTP)
        logging.info("Initiating AWS Login, This authenticates against your chosen profile")
        mfa_TOTP = str(input("Enter the MFA code: "))

        response = sts_default_provider_chain.assume_role(
            RoleArn=aws_role_arn,
            RoleSessionName='aws_login',
            SerialNumber=aws_mfa_arn,
            TokenCode=mfa_TOTP
        )
        creds = response['Credentials']

        logging.warning(f"\nexport AWS_ACCESS_KEY_ID={creds['AccessKeyId']}"
                        f"\nexport AWS_SECRET_ACCESS_KEY={creds['SecretAccessKey']}"
                        f"\nexport AWS_SESSION_TOKEN={creds['SessionToken']}")

        if not profile:
            return boto3.session.Session(region_name=aws_region,
                                         aws_access_key_id=creds['AccessKeyId'],
                                         aws_secret_access_key=creds['SecretAccessKey'],
                                         aws_session_token=creds['SessionToken'])

        return boto3.session.Session(region_name=aws_region,
                                     profile_name=profile,
                                     aws_access_key_id=creds['AccessKeyId'],
                                     aws_secret_access_key=creds['SecretAccessKey'],
                                     aws_session_token=creds['SessionToken'])

    def secrets_manager_client(self):
        aws_region = self.data['aws']['region']
        self.client = self.session.client(
            service_name='secretsmanager',
            region_name=aws_region
        )

    def ssm_client(self):
        aws_region = self.data['aws']['region']
        self.client = self.session.client(
            service_name='ssm',
            region_name=aws_region
        )

    def cfn_client(self):
        aws_region = self.data['aws']['region']
        self.client = self.session.client(
            service_name='cloudformation',
            region_name=aws_region
        )
        print(f'Client currently: {self.client}')

    def cfn_describe_stack(self, stack_name):
        try:
            response = self.client.describe_stacks(StackName=stack_name)
        except (ClientError, NoCredentialsError):
            logging.warning(f'Service: {stack_name} doesnt have cloud template profile :: Skipping')
            return None
        return response['Stacks'][0]

    def cfn_get_template(self, stack_id):
        try:
            response = self.client.get_template(
                StackName=stack_id,
                TemplateStage='Processed'
            )
        except (ClientError, NoCredentialsError):
            logging.error(f'Service: {stack_id} doesnt have cloud template profile :: Skipping')
            return None
        return response['TemplateBody']

    def cfn_describe_resources(self, stack_id):
        try:
            response = self.client.describe_stack_resources(
                StackName=stack_id
                )
        except (ClientError, NoCredentialsError):
            logging.error(f'Service: {stack_id} cannot retrieve resources :: Skipping')
            return None

        return response['StackResources']

    def cfn_drift_detect_id(self, stack_id):
        try:
            response = self.client.detect_stack_drift(
                StackName=stack_id
                )
        except (ClientError, NoCredentialsError):
            logging.error(f'Service: {stack_id} Cannot Detect stack drift :: Skipping')
            return None

        return response['StackDriftDetectionId']

    def cfn_drift_detect_status(self, stack_drift_id):
        try:
            response = self.client.describe_stack_drift_detection_status(
                StackDriftDetectionId=stack_drift_id
                )
        except (ClientError, NoCredentialsError):
            logging.error(f'Service: {stack_drift_id} does not seem to exist :: Skipping')
            return None

        return response

    def cfn_stack_resource_drifts(self, stack_id, next_token=None):
        stack_drift_filters = [
            'IN_SYNC',
            'MODIFIED',
            'DELETED',
            'NOT_CHECKED'
        ]
        if not next_token:
            response = self.client.describe_stack_resource_drifts(
                StackName=stack_id,
                StackResourceDriftStatusFilters=stack_drift_filters,
                MaxResults=100,
            )
        else:
            response = self.client.describe_stack_resource_drifts(
                StackName=stack_id,
                StackResourceDriftStatusFilters=stack_drift_filters,
                MaxResults=100,
                NextToken=next_token
            )

        return response

    def cfn_update_stack(self, stack_id, template, capabilities=None, params=None):
        if not isinstance(template, str):
            template = json.dumps(template)
        if not capabilities:
            capabilities = [
                'CAPABILITY_NAMED_IAM',
                'CAPABILITY_AUTO_EXPAND'
            ]
        response = self.client.update_stack(
            StackName=stack_id,
            TemplateBody=template,
            Capabilities=capabilities,
            Parameters=params
        )
        return response

    def cfn_create_changeset(self, stack_name, template, resources, params=None,
                             changeset_name=None, changeset_type=None, capabilities=None):
        if not isinstance(template, str):
            template = json.dumps(template)
        if not capabilities:
            capabilities = [
                'CAPABILITY_NAMED_IAM',
                'CAPABILITY_AUTO_EXPAND'
            ]
        if not changeset_type:
            changeset_type = 'IMPORT'
        if not changeset_name:
            changeset_name = 'Stack-Rename-' + str(int(time.time()))
        response = self.client.create_change_set(
            StackName=stack_name,
            ChangeSetName=changeset_name,
            TemplateBody=template,
            ChangeSetType=changeset_type,
            Capabilities=capabilities,
            ResourcesToImport=resources,
            Parameters=params
        )
        return response["StackId"], response

    def cfn_exec_changeset(self, changeset_name, stack_id):
        response = self.client.execute_change_set(
            ChangeSetName=changeset_name,
            StackName=stack_id
        )
        return response

    def cfn_list_imports(self, export_name, next_token=None):
        if not next_token:
            response = self.client.list_imports(
                ExportName=export_name,
            )
        else:
            response = self.client.list_imports(
                ExportName=export_name,
                NextToken=next_token
            )
        #return response['Imports'], response['NextToken']
        return response

    def cfn_list_exports(self, next_token=None):
        if not next_token:
            response = self.client.list_exports()
        else:
            response = self.client.list_exports(
                NextToken=next_token
            )
        return response

    def cfn_delete_stack(self, stack_id):
        response = self.client.delete_stack(
            StackName=stack_id
        )
        return response

    def cfn_waiter(self, stack_id, waiter_type, changeset_name=None, delay=None, attempts=None):
        if not attempts:
            attempts = 360
        if not delay:
            delay = 10

        waiter_config = {
            'Delay': delay,
            'MaxAttempts': attempts
        }

        waiter = self.client.get_waiter(waiter_type)

        if changeset_name:
            waiter.wait(
                StackName=stack_id,
                ChangeSetName=changeset_name,
                WaiterConfig=waiter_config
            )
        else:
            waiter.wait(
                StackName=stack_id,
                WaiterConfig=waiter_config
            )

    def get_secret(self, secret=None):
        secret_data = {}
        secret_name = secret.lower()

        try:
            response = self.client.get_secret_value(SecretId=secret_name)
        except ClientError as list_e:
            if list_e.response['Error']['Code'] == 'DecryptionFailureException':
                logging.error('Secrets Manager cannot decrypt the protected secret text using the provided KMS key')
                exit(1)
            elif list_e.response['Error']['Code'] == 'AccessDeniedException':
                logging.error('Access Denied')
                exit(1)
            elif list_e.response['Error']['Code'] == 'ResourceNotFoundException':
                logging.warning(f'secret: {secret_name} not found :: skipping entry')
                exit(1)
            else:
                raise list_e
        else:
            if 'SecretString' in response:
                secret = response['SecretString']
            else:
                secret = base64.b64decode(response['SecretBinary'])

        try:
            secret_data[secret_name] = json.loads(secret)
        except (TypeError, ValueError):
            secret_data[secret_name] = secret

        return secret_data
