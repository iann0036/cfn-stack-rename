#!/usr/bin/env python3

from libs import file_handler, cfn_resource_identifiers
from pprint import pprint

__version__ = '0.1'

io_handle = file_handler.FileHandler()

resources = dict()
resources['resource_identifiers'] = dict()
resources['resource_identifiers'] = cfn_resource_identifiers.resources()

pprint(resources)

io_handle.write_json(output_file="configs/cloudformation.json", data=resources)
io_handle.write_yaml(output_file="configs/cloudformation.yaml", data=resources)





