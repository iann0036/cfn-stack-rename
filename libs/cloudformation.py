import logging
import time
from pprint import pprint
import json
from cfn_flip import to_json
from copy import deepcopy


def verify_action(action, stack_name):
    logging.warning(f'You are about to perform: {action} on stack: {stack_name}')
    read_input = str(input('Are you sure you want to continue? (YES to do so): '))
    if read_input != 'YES':
        logging.warning('Skipping step as requested')
        return False
    return True


def stack_exports(stack_desc):
    exports = dict()
    for outputs in stack_desc['Outputs']:
        if 'ExportName' in outputs:
            exports[outputs['ExportName']] = outputs['OutputValue']
    logging.info(f"Stack Exports currently: {exports}")
    return exports


def stacks_importing_exports(aws_client, exports):
    stacks_importing = dict()
    for export_name, export_value in exports.items():
        response = aws_client.cfn_list_imports(export_name)
        for stack in response['Imports']:
            if stack not in stacks_importing:
                stacks_importing[stack] = list()
            stacks_importing[stack].append(export_name)

        while 'NextToken' in response:
            token = response['NextToken']
            response = aws_client.cfn_list_imports(export_name, next_token=token)
            for stack in response['Imports']:
                if stack not in stacks_importing:
                    stacks_importing[stack] = list()
                stacks_importing[stack].append(export_name)

    if len(stacks_importing) > 1:
        logging.error(f'The Following stacks are importing resources from this stack:')
        for stack_name, stack_imports in stacks_importing.items():
            for import_name in stack_imports:
                logging.error(f'  * Stack Name: {stack_name}: :: Import: {import_name} '
                              f':: Actual Value: {exports[import_name]}')
        logging.error(f'Please update the stacks listed with the actual value provided above '
                      f'instead of the import name before continuing')
        logging.error(f'This will ensure the stack can be renamed without issue')
        continue_regardless = str(input(f'Do you wish to continue - '
                                        f'even though this is guaranteed to fail? (Yes/no): '))
        if continue_regardless != 'YES':
            logging.info('Wise Choice, exiting now')
            exit(0)

    return stacks_importing


def remove_imports_from_stack_templates(aws_client, stacks_importing, exports):
    stack_params = []
    for stack_name, stack_imports in stacks_importing.items():
        for import_name in stack_imports:
            stack_desc = aws_client.cfn_describe_stack(stack_name=stack_name)
            stack_id = stack_desc['StackId']  # original_stack_id
            if 'Parameters' in stack_desc:
                stack_params = stack_desc['Parameters']
            stack_template =  aws_client.cfn_get_template(stack_id=stack_id)
            if not isinstance(stack_template, str):
                stack_template = json.dumps(dict(stack_template))
            template = json.loads(to_json(stack_template))
            # this is the point you realise that cloudformation absolutely sucks.
            # hey if the amount of code required to just rename a stack wasn't already
            # an indication...
            # we can do a recursive / tree lookup through the template but
            # if the imported value is using sub then matching against it
            # is difficult - everyone uses different patterns so cant do a generic thing
            # basically you can never fully trust it - its just not worth the effort.
            # could add possibly a config parameter for user to define the pattern
            # if they use sub for their imports etc - probably cleanest way of doing it
            # too much effort for now.
            pprint(template)


def detect_drift(aws_client, stack_id):
    stack_drift_id = aws_client.cfn_drift_detect_id(stack_id)
    stack_drift_status = aws_client.cfn_drift_detect_status(stack_drift_id)
    resource_drifts = []

    logging.info(f'Found Stack: {stack_id} :: Detecting drift...')

    while stack_drift_status['DetectionStatus'] == "DETECTION_IN_PROGRESS":
        time.sleep(4)
        stack_drift_status = aws_client.cfn_drift_detect_status(stack_drift_id)

    if stack_drift_status['DetectionStatus'] != "DETECTION_COMPLETE" or stack_drift_status[
        'StackDriftStatus'] != "DRIFTED":
        if stack_drift_status['StackDriftStatus'] != "IN_SYNC":
            logging.error("Could not determine drift results")
            raise ValueError("Drift Results Undetermined")

    resource_drifts_result = aws_client.cfn_stack_resource_drifts(stack_id)
    resource_drifts += resource_drifts_result['StackResourceDrifts']

    while 'NextToken' in resource_drifts_result:
        token = resource_drifts_result['NextToken']
        resource_drifts_result = aws_client.cfn_stack_resource_drifts(stack_id, next_token=token)
        resource_drifts += resource_drifts_result['StackResourceDrifts']

    # logging.info(f"Resource Drifts: {pprint(resource_drifts)}")
    return resource_drifts


def sanitize_template(data, template, resources, drifts):
    supported_imports = dict()
    non_importables = dict()
    non_driftables = dict()
    resource_identifiers = data['cloudformation']['resource_identifiers']
    sanitized_template = deepcopy(template)

    for k, v in template['Resources'].items():
        found = False
        resource_exists = False
        # logging.info(f'Template resource scanning currently key:{k} ::  value:{v}')

        for deployed_resource in resources:
            if k == deployed_resource['LogicalResourceId']:
                resource_exists = True

        if not resource_exists and 'Condition' in template['Resources'][k]:  # skip conditionals
            continue

        for i in range(len(drifts)):
            if drifts[i]['LogicalResourceId'] == k:
                found = True
                break
        if not found:
            logging.warning(f'Found resource: {k} type without drift info: {template["Resources"][k]["Type"]}')
            non_driftables[k] = template["Resources"][k]["Type"]
        if template['Resources'][k]['Type'] not in resource_identifiers.keys():
            logging.warning(f'Found non-importable resource: {k} type: {template["Resources"][k]["Type"]} '
                            f'This resource will need to be recreated')
            non_importables[k] = template["Resources"][k]["Type"]
            del sanitized_template['Resources'][k]
        if template['Resources'][k]['Type'] in resource_identifiers.keys():
            logging.info(f'Resource: {k} Can be imported')
            if k not in supported_imports.keys():
                supported_imports[k] = template['Resources'][k]['Type']

    logging.info(f'Supported imports: {supported_imports}')
    logging.info(f'Unsupported imports: {non_importables}')
    logging.info(f'Unsupported drifts: {non_driftables}')
    return supported_imports, non_importables, non_driftables, sanitized_template


def sanitize_resources(data, drifts, template):
    import_resources = []
    resource_identifiers = data['cloudformation']['resource_identifiers']
    sanitized_template = deepcopy(template)
    for drifted_resource in drifts:
        resource_identifier = {}

        import_properties = resource_identifiers[drifted_resource['ResourceType']]['importProperties'].copy()
        if 'PhysicalResourceIdContext' in drifted_resource:
            for prop in drifted_resource['PhysicalResourceIdContext']:
                if prop['Key'] in import_properties:
                    resource_identifier[prop['Key']] = prop['Value']
                    import_properties.remove(prop['Key'])

        if len(import_properties) > 1:
            logging.error(f'{drifted_resource}: Unexpected additional '
                          f'importable keys required {import_properties}, aborting...')
            quit()
        elif len(import_properties) == 1:
            resource_identifier[import_properties[0]] = drifted_resource['PhysicalResourceId']

        sanitized_template['Resources'][drifted_resource['LogicalResourceId']] = {
            'DeletionPolicy': 'Retain',
            'Type': drifted_resource['ResourceType'],
            'Properties': json.loads(drifted_resource['ActualProperties'])
        }

        import_resources.append({
            'ResourceType': drifted_resource['ResourceType'],
            'LogicalResourceId': drifted_resource['LogicalResourceId'],
            'ResourceIdentifier': resource_identifier
        })
    return sanitized_template, import_resources


def set_resource_retention(template, supported_resources):
    retain_template = deepcopy(template)
    pprint(supported_resources)
    for resource in supported_resources:
        retain_template['Resources'][resource]['DeletionPolicy'] = 'Retain'
        logging.info(f'Added Retain Deletion Policy to resource: {resource}')

    logging.info(f'Added Retain Policy to all supported resources')
    return retain_template
