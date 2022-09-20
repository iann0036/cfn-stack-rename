from copy import deepcopy
import logging


def verify_import(res_type):
    read_input = str(input(f'do you want to remove all: {res_type} from importing? (yes to do so): '))
    if read_input.lower() != 'yes':
        logging.info(f'Leaving {res_type} intact')
        return False
    logging.info(f'Removing {res_type} from import process')
    return True


def recover_data(supported_resources, sanitized_template, change_set_data):

    sanitized_copy = deepcopy(sanitized_template)
    for res_type in list(set(supported_resources.values())):
        logging.info(f'Checking {res_type}  - did this fail to import?')
        verify_result = verify_import(res_type)

        if verify_result:
            change_set_data[:] = (data for data in change_set_data if data['ResourceType'] != res_type)
            for tr_name,  tr_val in sanitized_template['Resources'].items():
                if tr_val['Type'] == res_type:
                    del sanitized_copy['Resources'][tr_name]

    return change_set_data, sanitized_copy







