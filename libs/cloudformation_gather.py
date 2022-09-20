import logging
import time
import json
from cfn_flip import to_json
from copy import deepcopy


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
        if not response:
            logging.info("Good News: This Stack does not have any exports imported by other stacks")
            continue
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
                                        f'even though this is guaranteed to fail? (YES to do so): '))
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
            stack_template = aws_client.cfn_get_template(stack_id=stack_id)
            if not isinstance(stack_template, str):
                stack_template = json.dumps(dict(stack_template))
            template = json.loads(to_json(stack_template))
            # We can do a recursive / tree lookup through the template but
            # if the imported value is using sub then matching against it
            # is difficult - everyone uses different patterns so cant do a generic thing
            # could add possibly a config parameter for user to define the pattern
            # if they use sub for their imports for example - probably the cleanest
            # way of doing it - too much effort for now.


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
        logging.debug(f'Template resource scanning currently key:{k} ::  value:{v}')

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

    # removing all entries from non_driftables that also do not support importing:
    for resource in non_importables.keys():
        if resource in non_driftables.keys():
            logging.info(f"Removing {resource} from non_driftables this cannot be imported")
            del non_driftables[resource]
    logging.debug(f'Supported imports: {supported_imports}')
    logging.debug(f'Unsupported imports: {non_importables}')
    logging.debug(f'Unsupported drifts: {non_driftables}')
    return supported_imports, non_importables, non_driftables, sanitized_template


def sanitize_resources(data, drifts, template, supported_imports, undriftables, stack_desc_resources):
    import_resources = []
    import_resource_counter = 0
    resource_identifiers = data['cloudformation']['resource_identifiers']
    sanitized_template = deepcopy(template)
    logging.info(f'Sanitizing resources for creating change set...')

    for importable_resource in supported_imports.keys():
        sanitized_template['Resources'][importable_resource]['DeletionPolicy'] = 'Retain'
        logging.debug(f'Added Retain Deletion Policy to resource: {importable_resource}')

    # we cannot have a non-drifted resource with more than 1 import properties - no way of finding out
    # the other as stack_description_resources does not contain property values. 
    for stack_desc_resource in stack_desc_resources:
        if stack_desc_resource['LogicalResourceId'] in undriftables.keys():
            import_props = resource_identifiers[stack_desc_resource['ResourceType']]['importProperties'].copy()
            resource_id = dict()
            if len(import_props) > 1:
                logging.error(f'{stack_desc_resource}: Unexpected additional '
                              f'importable keys required {import_props}, aborting...')
                raise ValueError(f'Too many import properties: {import_props}, should only have 1')
            elif len(import_props) == 1:
                resource_id[import_props[0]] = stack_desc_resource['PhysicalResourceId']
            import_resources.append({
                'ResourceType': stack_desc_resource['ResourceType'],
                'LogicalResourceId': stack_desc_resource['LogicalResourceId'],
                'ResourceIdentifier': resource_id
            })
            logging.info(f'Added the following to import resources: '
                         f'{import_resources[import_resource_counter]}')
            import_resource_counter += 1

    for drifted_resource in drifts:
        resource_identifier = {}

        import_properties = resource_identifiers[drifted_resource['ResourceType']]['importProperties'].copy()
        if 'PhysicalResourceIdContext' in drifted_resource:
            for prop in drifted_resource['PhysicalResourceIdContext']:
                if prop['Key'] in import_properties:
                    resource_identifier[prop['Key']] = prop['Value']
                    import_properties.remove(prop['Key'])

        # This is wrong if there are 2 import_properties one of the import properties will be found as an id
        # within the drifted resource 'ExpectedProperties'. So need to check the import_properties match the key against
        # the key against the 'ExpectedProperties' assign the value from there and the 2nd key will by the PhysicalResourceId.
        if len(import_properties) > 2:
            logging.error(f'{drifted_resource}: Unexpected additional '
                          f'importable keys required {import_properties}, aborting...')
            raise ValueError(f'Too many import properties: {import_properties}, should only have 1')
        elif len(import_properties) == 2:
            resource_identifier[import_properties[0]] = drifted_resource['LogicalResourceId']
            resource_identifier[import_properties[1]] = drifted_resource['PhysicalResourceId']
        elif len(import_properties) == 1:
            resource_identifier[import_properties[0]] = drifted_resource['PhysicalResourceId']

        sanitized_template['Resources'][drifted_resource['LogicalResourceId']] = {
            'DeletionPolicy': 'Retain',
            'Type': drifted_resource['ResourceType'],
            'Properties': json.loads(drifted_resource['ActualProperties'])
        }
        logging.info(f'Updating stack resource: {drifted_resource["LogicalResourceId"]}')
        logging.debug(f'Updating stack resource as follows: '
                      f'{sanitized_template["Resources"][drifted_resource["LogicalResourceId"]]}')

        import_resources.append({
            'ResourceType': drifted_resource['ResourceType'],
            'LogicalResourceId': drifted_resource['LogicalResourceId'],
            'ResourceIdentifier': resource_identifier
        })
        logging.info(f'Added the following to import resources: '
                     f'{import_resources[import_resource_counter]}')
        import_resource_counter += 1
    return sanitized_template, import_resources


def set_resource_retention(template, supported_imports):
    retain_template = deepcopy(template)
    for resource in supported_imports.keys():
        retain_template['Resources'][resource]['DeletionPolicy'] = 'Retain'
        logging.info(f'Added Retain Deletion Policy to resource: {resource}')

    logging.info(f'Added Retain Policy to all supported resources')
    return retain_template
