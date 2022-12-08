#
##
##########################################################################
#                                                                        #
#       ecr_handler                                                      #
#                                                                        #
#       (c) Vamegh Hedayati                                              #
#                                                                        #
#       Please see https://github.com/vamegh/pylibs                      #
#                    for License Information                             #
#                             GNU/LGPL                                   #
##########################################################################
##
#
#  ecr_handler - This handles various ecr login functions

import base64
import docker
import logging
import subprocess

def set_ecr_credentials(data, session):
    aws_profiles = data['aws']['ecr_profiles']
    aws_region = data['aws']['region']

    ecr_client = session.client(
        service_name='ecr',
        region_name=aws_region)
    url_prefix = 'https://'

    try:
        token = ecr_client.get_authorization_token()
    except (ClientError, NoCredentialsError):
        logging.error(f"Sorry you do not have your aws ecr credentials configured\n"
                      f"Please configure this first, these are stored in ~/.aws/credentials. ")
        raise ValueError('AWS Token Not Found')

    user, passwd = base64.b64decode(token['authorizationData'][0]['authorizationToken']).decode().split(':')
    registry = token['authorizationData'][0]['proxyEndpoint']

    if registry.startswith(url_prefix):
        registry = registry[len(url_prefix):]
    auth_data = {"user": user, "pass": passwd, "registry": registry}
    logging.debug(f'Auth Data: {auth_data}')
    docker_registry_login(auth=auth_data)
    return auth_data


def docker_registry_login(auth=None):
    try:
        user = auth['user']
        passwd = auth['pass']
        url = auth['registry']
    except KeyError as err:
        logging.error(f"Error:  Docker Registry Login : Auth Details Issue: Error: {err}")

    docker_cli_cmd = f"docker login --username {user} --password {passwd} {url}".split()
    subprocess.Popen(docker_cli_cmd, stdout=None, stderr=None)
    docker_client = docker.from_env()
    login_status = docker_client.login(user, passwd, registry=url)
    logging.info(f"Docker Login Status: {login_status.get('Status')}")
    logging.info(f'\nDocker ECR Login Completed.\n\n')
