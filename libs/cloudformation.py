import logging
import time
from pprint import pprint
import json
from copy import deepcopy


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
    supported_import_list = []
    non_importable_list = []
    resource_identifiers = data['cloudformation']['resource_identifiers']
    # pprint(f'resource identifiers: {resource_identifiers.keys()}')
    # logging.warning(f'Stack Template:')
    # pprint(template)
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
            logging.warning(f'Found resource: {k} type without drift info: {template["Resources"][k]["Type"]} '
                            f'This resource will need to be recreated')
            non_importable_list.append(k)
            del sanitized_template['Resources'][k]
        elif template['Resources'][k]['Type'] not in resource_identifiers.keys():
            logging.warning(f'Found non-importable resource: {k} type: {template["Resources"][k]["Type"]} '
                            f'This resource will need to be recreated')
            non_importable_list.append(k)
            del sanitized_template['Resources'][k]
        else:
            logging.info(f'Resource: {k} Can be imported')
            if k not in supported_import_list:
                supported_import_list.append(k)

    logging.info(f'Supported import list: {supported_import_list}')
    logging.info(f'Unsupported list: {non_importable_list}')
    return supported_import_list, non_importable_list, sanitized_template


def sanitize_resources(data, drifts, template):
    import_resources = []
    resource_identifiers = data['cloudformation']['resource_identifiers']
    for drifted_resource in drifts:
        resource_identifier = {}

        import_properties = resource_identifiers[drifted_resource['ResourceType']]['importProperties'].copy()
        if 'PhysicalResourceIdContext' in drifted_resource:
            for prop in drifted_resource['PhysicalResourceIdContext']:
                if prop['Key'] in import_properties:
                    resource_identifier[prop['Key']] = prop['Value']
                    import_properties.remove(prop['Key'])

        if len(import_properties) > 1:
            logging.error("Unexpected additional importable keys required, aborting...")
            quit()
        elif len(import_properties) == 1:
            resource_identifier[import_properties[0]] = drifted_resource['PhysicalResourceId']

        template['Resources'][drifted_resource['LogicalResourceId']] = {
            'DeletionPolicy': 'Retain',
            'Type': drifted_resource['ResourceType'],
            'Properties': json.loads(drifted_resource['ActualProperties'])
        }

        import_resources.append({
            'ResourceType': drifted_resource['ResourceType'],
            'LogicalResourceId': drifted_resource['LogicalResourceId'],
            'ResourceIdentifier': resource_identifier
        })
    return template, import_resources


def set_resource_retention(template, supported_resources):
    for resource in supported_resources:
        template['Resources'][resource]['DeletionPolicy'] = 'Retain'
        logging.info(f'Added Retain Deletion Policy to resource: {resource}')

    logging.info(f'Added Retain Policy to all supported resources')
    return template
