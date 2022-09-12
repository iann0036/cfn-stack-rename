import boto3
import sys
import json
import time
import pprint
from collections import OrderedDict
from cfn_flip import flip, to_yaml, to_json
from libs import cfn_resource_identifiers

resolve_matches = {}


def resolvePropertyValue(prop, match_resources, replace_values):
    if isinstance(prop, dict):
        if 'Ref' in prop:
            if prop['Ref'] in match_resources:
                if replace_values:
                    return resolve_matches['Ref' + prop['Ref']]
                else:
                    resolve_matches['Ref' + prop['Ref']] = {
                        'Ref': prop['Ref']
                    }
        elif 'Fn::GetAtt' in prop:
            if prop['Fn::GetAtt'][0] in match_resources:
                if replace_values:
                    return resolve_matches['GetAtt' + prop['Fn::GetAtt'][0] + prop['Fn::GetAtt'][1]]
                else:
                    resolve_matches['GetAtt' + prop['Fn::GetAtt'][0] + prop['Fn::GetAtt'][1]] = {
                        'Fn::GetAtt': prop['Fn::GetAtt']
                    }
        elif 'Fn::Sub' in prop:
            pass  # TODO

        ret = {}
        for k, v in prop.items():
            ret[k] = resolvePropertyValue(v, match_resources, replace_values)
        return ret
    elif isinstance(prop, list) and not isinstance(prop, str):
        ret = []
        for listitem in prop:
            ret.append(resolvePropertyValue(listitem, match_resources, replace_values))
        return ret
    else:
        return prop


eligible_import_resources = cfn_resource_identifiers.resources()

if len(sys.argv) == 5:
    session = boto3.session.Session(profile_name=sys.argv[4])
    cfnclient = session.client('cloudformation', region_name=sys.argv[3])
elif len(sys.argv) == 4:
    cfnclient = boto3.client('cloudformation', region_name=sys.argv[3])
elif len(sys.argv) == 3:
    cfnclient = boto3.client('cloudformation')
else:
    print("Inconsistent arguments")
    quit()

try:
    stacks = cfnclient.describe_stacks(
        StackName=sys.argv[1]
    )['Stacks']
except:
    print("Could not find stack")
    quit()

original_stack_id = stacks[0]['StackId']
stack_name = stacks[0]['StackName']
new_stack_name = sys.argv[2]
stack_params = []
if 'Parameters' in stacks[0]:
    stack_params = stacks[0]['Parameters']

original_template = cfnclient.get_template(
    StackName=original_stack_id,
    TemplateStage='Processed'
)['TemplateBody']

original_resources = cfnclient.describe_stack_resources(
    StackName=original_stack_id
)['StackResources']

if not isinstance(original_template, str):
    original_template = json.dumps(dict(original_template))  # OrderedDict

print("Found stack, detecting drift...")

stack_drift_detection_id = cfnclient.detect_stack_drift(
    StackName=original_stack_id
)['StackDriftDetectionId']

stack_drift_detection_status = cfnclient.describe_stack_drift_detection_status(  # no waiter :(
    StackDriftDetectionId=stack_drift_detection_id
)
while stack_drift_detection_status['DetectionStatus'] == "DETECTION_IN_PROGRESS":
    time.sleep(5)
    stack_drift_detection_status = cfnclient.describe_stack_drift_detection_status(
        StackDriftDetectionId=stack_drift_detection_id
    )

if stack_drift_detection_status['DetectionStatus'] != "DETECTION_COMPLETE" or stack_drift_detection_status[
    'StackDriftStatus'] != "DRIFTED":
    if stack_drift_detection_status['StackDriftStatus'] != "IN_SYNC":
        print("Could not determine drift results")
        quit()

resource_drifts = []
resource_drifts_result = cfnclient.describe_stack_resource_drifts(
    StackName=original_stack_id,
    StackResourceDriftStatusFilters=[
        'IN_SYNC',
        'MODIFIED',
        'DELETED',
        'NOT_CHECKED'
    ],
    MaxResults=100
)
resource_drifts += resource_drifts_result['StackResourceDrifts']
while 'NextToken' in resource_drifts_result:
    resource_drifts_result = cfnclient.describe_stack_resource_drifts(
        StackName=original_stack_id,
        StackResourceDriftStatusFilters=[
            'IN_SYNC',
            'MODIFIED',
            'DELETED',
            'NOT_CHECKED'
        ],
        NextToken=resource_drifts_result['NextToken'],
        MaxResults=100
    )
    resource_drifts += resource_drifts_result['StackResourceDrifts']

template = json.loads(to_json(original_template))

# check all is in drift results
for k, v in template['Resources'].items():
    found = False
    resource_exists = False

    for deployed_resource in original_resources:
        if k == deployed_resource['LogicalResourceId']:
            resource_exists = True

    if not resource_exists and 'Condition' in template['Resources'][k]:  # skip conditionals
        continue

    for i in range(len(resource_drifts)):
        if resource_drifts[i]['LogicalResourceId'] == k:
            found = True
            break
    if not found:
        print("Found resource type without drift info: " + template['Resources'][k]['Type'] + ", aborting")
        quit()
    if template['Resources'][k]['Type'] not in eligible_import_resources.keys():
        print("Found non-importable resource type: " + template['Resources'][k]['Type'] + ", aborting")
        quit()

for k, v in template['Resources'].items():
    template['Resources'][k]['DeletionPolicy'] = 'Retain'

print("Setting resource retention...")

#cfnclient.update_stack(
#    StackName=original_stack_id,
#    TemplateBody=json.dumps(template),
#    Capabilities=[
#        'CAPABILITY_NAMED_IAM',
#        'CAPABILITY_AUTO_EXPAND'
#    ],
#    Parameters=stack_params
#)

#waiter = cfnclient.get_waiter('stack_update_complete')
#waiter.wait(
#    StackName=original_stack_id,
#    WaiterConfig={
#        'Delay': 10,
#        'MaxAttempts': 360
#    }
#)

import_resources = []
for drifted_resource in resource_drifts:
    resource_identifier = {}

    import_properties = eligible_import_resources[drifted_resource['ResourceType']]['importProperties'].copy()
    if 'PhysicalResourceIdContext' in drifted_resource:
        for prop in drifted_resource['PhysicalResourceIdContext']:
            if prop['Key'] in import_properties:
                resource_identifier[prop['Key']] = prop['Value']
                import_properties.remove(prop['Key'])

    if len(import_properties) > 1:
        print("ERROR: Unexpected additional importable keys required, aborting...")
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

print("Removing original stack (whilst retaining resources!)...")

#cfnclient.delete_stack(
#    StackName=original_stack_id
#)

#waiter = cfnclient.get_waiter('stack_delete_complete')
#waiter.wait(
#    StackName=original_stack_id,
#    WaiterConfig={
#        'Delay': 10,
#        'MaxAttempts': 360
#    }
#)

print("Recreating stack with imported resources...")

template.pop('Outputs', None)

change_set_name = 'Stack-Rename-' + str(int(time.time()))
#new_stack_id = cfnclient.create_change_set(
#    StackName=new_stack_name,
#    ChangeSetName=change_set_name,
#    TemplateBody=json.dumps(template),
#    ChangeSetType='IMPORT',
#    Capabilities=[
#        'CAPABILITY_NAMED_IAM',
#        'CAPABILITY_AUTO_EXPAND'
#    ],
#    ResourcesToImport=import_resources,
#    Parameters=stack_params
#)['StackId']

#waiter = cfnclient.get_waiter('change_set_create_complete')
#waiter.wait(
#    StackName=new_stack_id,
#    ChangeSetName=change_set_name,
#    WaiterConfig={
#        'Delay': 10,
#        'MaxAttempts': 360
#    }
#)

#cfnclient.execute_change_set(
#    ChangeSetName=change_set_name,
#    StackName=new_stack_id
#)

#waiter = cfnclient.get_waiter('stack_import_complete')
#waiter.wait(
#    StackName=new_stack_id,
#    WaiterConfig={
#        'Delay': 10,
#        'MaxAttempts': 360
#    }
#)

print("Cleaning up...")

#cfnclient.update_stack(
#    StackName=new_stack_id,
#    TemplateBody=original_template,
#    Capabilities=[
#        'CAPABILITY_NAMED_IAM',
#        'CAPABILITY_AUTO_EXPAND'
#    ],
#    Parameters=stack_params
#)

#waiter = cfnclient.get_waiter('stack_update_complete')
#waiter.wait(
#    StackName=new_stack_id,
#    WaiterConfig={
#        'Delay': 10,
#        'MaxAttempts': 360
#    }
#)

print("Succcessfully renamed stack")
