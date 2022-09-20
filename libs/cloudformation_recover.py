from copy import deepcopy
import logging


def verify_import(res_type):
    read_input = str(input(f'do you want to remove all resources of type: {res_type} from importing? (yes to do so): '))
    if read_input.lower() != 'yes':
        logging.info(f'Leaving {res_type} intact')
        return False
    logging.info(f'Removing {res_type} from import process')
    return True


def verify_action(action, stack_name):
    logging.warning(f'You are about to perform: {action} on stack: {stack_name}')
    read_input = str(input('Are you sure you want to continue? (YES to do so): '))
    if read_input != 'YES':
        logging.info('Skipping step as requested')
        return False
    return True


def verify_error():
    logging.warning(f'An error occurred displayed above - this may just mean the operation has already been done')
    read_input = str(input('Do you wish to continue? (YES to do so): '))
    if read_input != 'YES':
        logging.info('Exiting as requested')
        exit(1)
    return True


def verify_drift(resource, property):
    r_name = resource['LogicalResourceId']
    r_type = resource['ResourceType']
    logging.info(f'Resource: {r_name}, Type: {r_type}, drift detected for property: {property},'
                 f' not in actual_properties. For some resources like lambda functions, '
                 f' deployed using SAM, it is best to ignore the drift')
    read_input = str(input(f'Ignore drift for resource: {r_name}? (yes to do so): '))
    if read_input.lower() != 'yes':
        logging.info('Updating resource to use actual properties')
        return False
    logging.info('Updating resource to use expected properties')
    return True


def recover_data(supported_resources, sanitized_template, change_set_data):
    sanitized_copy = deepcopy(sanitized_template)
    resources_kept = list()
    resources_removed = dict()
    for res_type in list(set(supported_resources.values())):
        logging.info(f'Checking {res_type}  - did this fail to import?')
        verify_result = verify_import(res_type)

        if verify_result:
            change_set_data[:] = (data for data in change_set_data if data['ResourceType'] != res_type)
            for tr_name, tr_val in sanitized_template['Resources'].items():
                if tr_val['Type'] == res_type:
                    del sanitized_copy['Resources'][tr_name]
                    resources_removed[tr_name] = tr_val['Type']

        if not verify_result:
            resources_kept.append(res_type)

    logging.info('"The following resource types have been kept in the change set:')
    for rk_type in resources_kept:
        logging.info(f'  * {rk_type}')
    logging.warning('"The following resources have been removed from the change set:')
    for rr_name, rr_type in resources_removed.items():
        logging.info(f'  * {rr_name} : {rr_type}')

    return change_set_data, sanitized_copy, resources_removed


def depends_on_data(resources_removed, template):
    template_copy = deepcopy(template)

    # This is 1 dependency I know exists - this function really needs to be smarter,
    # but it really is difficult without working out all the interdependent relationships that can exist.
    # api gateways that use lambdas require the lambdas to exist before api gateway can be deployed / updated.

    for sr_name, sr_type in resources_removed.items():
        if sr_type == "AWS::Lambda::Function" or sr_type == "AWS::Lambda::Alias" or sr_type == "AWS::Lambda::Version":
            for tr_name, tr_val in template['Resources'].items():
                if tr_val['Type'] == 'AWS::ApiGateway::Deployment':
                    if 'DependsOn' not in template_copy['Resources'][tr_name]:
                        template_copy['Resources'][tr_name]['DependsOn'] = list()
                    template_copy['Resources'][tr_name]['DependsOn'].append(sr_name)
    return template_copy
